# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import sys
from pymongo import MongoClient
import logging

from wsgidav import util, wsgidav_app, compat
from wsgidav.util import join_uri
from wsgidav.dav_error import DAVError, HTTP_NOT_FOUND, HTTP_FORBIDDEN
from wsgidav.dc.base_dc import BaseDomainController
from wsgidav.dav_provider import DAVProvider
from wsgidav.fs_dav_provider import FolderResource, FileResource, DAVNonCollection, DAVCollection

from inginious.common import custom_yaml
from inginious.common.filesystems.local import LocalFSProvider
from inginious.frontend.user_manager import UserManager
from inginious.frontend.session_mongodb import MongoStore
from inginious.frontend.courses import WebAppCourse


class FakeIO(object):
    """ Fake fd-like object """
    def __init__(self):
        self._content = None

    def write(self, content):
        self._content = content

    def close(self):
        pass

    def getvalue(self):
        return self._content


def get_dc(database, user_manager, filesystem):

    class INGIniousDAVDomainController(BaseDomainController):
        """ Authenticates users using the API key and their username """
        def __init__(self, wsgidav_app, config):
            super(INGIniousDAVDomainController, self).__init__(wsgidav_app, config)

        def __repr__(self):
            return self.__class__.__name__

        def get_domain_realm(self, pathinfo, environ):
            """Resolve a relative url to the  appropriate realm name."""
            # we don't get the realm here, its already been resolved in
            # request_resolver
            if pathinfo.startswith("/"):
                pathinfo = pathinfo[1:]
            parts = pathinfo.split("/")
            return parts[0]

        def require_authentication(self, realm, environ):
            """Return True if this realm requires authentication or False if it is
            available for general access."""
            course = database.courses.find_one({"_id": realm})
            if not course:
                return False
            return True

        def supports_http_digest_auth(self):
            # We have access to a plaintext password (or stored hash)
            return True

        def basic_auth_user(self, realmname, username, password, environ):
            """Returns True if this username/password pair is valid for the realm,
            False otherwise. Used for basic authentication."""
            course = database.courses.find_one({"_id": realmname})
            if not course:
                raise DAVError(HTTP_NOT_FOUND, "Could not find '{}'".format(realmname))
            course = WebAppCourse(course["_id"], course, filesystem, None)
            if not user_manager.has_admin_rights_on_course(course, username=username):
                return False
            apikey = user_manager.get_user_api_key(username, create=None)
            return apikey is not None and password == apikey

        def digest_auth_user(self, realm, user_name, environ):
            """Computes digest hash A1 part."""
            password = user_manager.get_user_api_key(user_name, create=True)
            return self._compute_http_digest_a1(realm, user_name, password)

    return INGIniousDAVDomainController


class INGIniousTaskFile(DAVNonCollection):
    """ Protects the course description file. """
    def __init__(self, path, environ, course_id, task_id):
        DAVNonCollection.__init__(self, path, environ)
        self._database = self.provider.database
        self._course_id = course_id
        self._task_id = task_id
        self._content = FakeIO()

    def support_recursive_delete(self):
        return False

    def get_content_length(self):
        return len(self.get_content().read())

    def get_content_type(self):
        return "text/yaml"

    def get_content(self):
        task_desc = self._database.tasks.find_one({"courseid": self._course_id, "taskid": self._task_id})
        if task_desc:
            del task_desc["courseid"]
            del task_desc["taskid"]
            del task_desc["_id"]
            logger = logging.getLogger("inginious.webdav")
            logger.info("Exporting task {}/{}".format(self._course_id, self._task_id))
            return compat.BytesIO(custom_yaml.dump(task_desc).encode("utf-8"))
        return compat.BytesIO(b"")

    def delete(self):
        """ It is forbidden to delete a course description file"""
        self._database.tasks.delete_one({"courseid": self._course_id, "taskid": self._task_id})
        self.remove_all_properties(True)
        self.remove_all_locks(True)

    def copy_move_single(self, dest_path, is_move):
        """ It is forbidden to delete a course description file"""
        raise DAVError(HTTP_FORBIDDEN)

    def move_recursive(self, dest_path):
        """ It is forbidden to delete a course description file"""
        raise DAVError(HTTP_FORBIDDEN)

    def begin_write(self, content_type=None):
        return self._content

    def end_write(self, with_errors):
        """ Update the course.yaml if possible. Verifies the content first, and make backups beforehand. """
        logger = logging.getLogger("inginious.webdav")
        logger.info("Importing task {}/{}".format(self._course_id, self._task_id))
        task_desc = custom_yaml.load(self._content.getvalue())
        task_desc["courseid"] = self._course_id
        task_desc["taskid"] = self._task_id
        if self._database.tasks.find_one({"courseid": self._course_id, "taskid": self._task_id}):
            self._database.tasks.replace_one({"courseid": self._course_id, "taskid": self._task_id}, task_desc)
        else:
            self._database.tasks.insert(task_desc)


class TaskFilesFolder(FolderResource):
    def get_display_name(self):
        return "files"


class TaskFolder(DAVCollection):
    def __init__(self, path, environ, courseid, taskid):
        DAVCollection.__init__(self, path, environ)
        self.filesystem = self.provider.filesystem
        self.database = self.provider.database
        self.courseid = courseid
        self.taskid = taskid

    def get_member_names(self):
        return ["files", "task.yaml"]

    def get_member(self, name):
        if name == "task.yaml":
            return INGIniousTaskFile(join_uri(self.path, name), self.environ, self.courseid, self.taskid)
        else:
            task_fs = self.filesystem.from_subfolder(self.courseid).from_subfolder(self.taskid)
            fp = os.path.abspath(task_fs.prefix)
            return TaskFilesFolder(join_uri(self.path, name), self.environ, fp)

class CourseFolder(DAVCollection):
    def __init__(self, path, environ, courseid):
        DAVCollection.__init__(self, path, environ)
        self.filesystem = self.provider.filesystem
        self.database = self.provider.database
        self.courseid = courseid

    def get_member_names(self):
        task_list = self.database.tasks.find({"courseid": self.courseid})
        task_list = list(task_list)
        return [task["taskid"] for task in task_list]

    def get_member(self, name):
        task = self.database.tasks.find_one({"courseid": self.courseid, "taskid": name})
        return TaskFolder(join_uri(self.path, name), self.environ, self.courseid, task["taskid"]) if task else None

    def create_collection(self, name):
        self.database.tasks.insert({"courseid": self.courseid,
                                    "taskid": name,
                                    "name": name,
                                    "problems": {},
                                    "environment": "default"})
        course_fs = self.filesystem.from_subfolder(self.courseid)
        task_fs = course_fs.from_subfolder(name)
        task_fs.ensure_exists()
        return TaskFolder(join_uri(self.path, name), self.environ, self.courseid, name)

class CourseCollection(DAVCollection):
    """Root collection, lists all mongo databases."""

    def __init__(self, path, environ):
        DAVCollection.__init__(self, path, environ)
        self.database = self.provider.database

    def get_member_names(self):
        course_list = self.database.courses.find()
        return [course["_id"] for course in course_list]

    def get_member(self, name):
        course = self.database.courses.find_one({"_id": name})
        return CourseFolder(join_uri(self.path, name), self.environ, course["_id"]) if course else None


class INGIniousFilesystemProvider(DAVProvider):
    """ A DAVProvider adapted to the structure of INGInious """
    def __init__(self, database, filesystem):
        super(INGIniousFilesystemProvider, self).__init__()
        self.database = database
        self.filesystem = filesystem
        self.readonly = False

    def is_readonly(self):
        return False

    def get_resource_inst(self, path, environ):
        self._count_get_resource_inst += 1
        root = CourseCollection("/", environ)
        return root.resolve("/", path)


def get_app(config):
    """ Init the webdav app """
    mongo_client = MongoClient(host=config.get('mongo_opt', {}).get('host', 'localhost'))
    database = mongo_client[config.get('mongo_opt', {}).get('database', 'INGInious')]

    # Create the FS provider
    if "tasks_directory" not in config:
        raise RuntimeError("WebDav access is only supported if INGInious is using a local filesystem to access tasks")

    fs_provider = LocalFSProvider(config["tasks_directory"])
    user_manager = UserManager(MongoStore(database, 'sessions'), database, config.get('superadmins', []))

    config = dict(wsgidav_app.DEFAULT_CONFIG)
    config["provider_mapping"] = {"/": INGIniousFilesystemProvider(database, fs_provider)}
    config["http_authenticator"]["domain_controller"] = get_dc(database, user_manager, fs_provider)
    config["http_authenticator"]["accept_basic"] = True
    config["verbose"] = 0

    app = wsgidav_app.WsgiDAVApp(config)
    util.init_logging(config)

    return app