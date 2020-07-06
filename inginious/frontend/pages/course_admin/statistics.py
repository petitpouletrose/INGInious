# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Utilities for computation of statistics  """
import json

from inginious.frontend.pages.course_admin.utils import INGIniousSubmissionAdminPage
from datetime import datetime, date, timedelta
import web


class CourseStatisticsPage(INGIniousSubmissionAdminPage):
    def _tasks_stats(self, courseid, tasks, daterange):
        stats_tasks = self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, "courseid": courseid}},
             {"$project": {"taskid": "$taskid", "result": "$result"}},
             {"$group": {"_id": "$taskid", "submissions": {"$sum": 1}, "validSubmissions":
                 {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}}}
              },
             {"$sort": {"submissions": -1}}])

        return [
            {"name": tasks[x["_id"]].get_name(self.user_manager.session_language()) if x["_id"] in tasks else x["_id"],
             "submissions": x["submissions"],
             "validSubmissions": x["validSubmissions"]}
            for x in stats_tasks
        ]

    def _users_stats(self, courseid, daterange):
        stats_users = self.database.submissions.aggregate([
            {"$match": {"submitted_on": {"$gte": daterange[0], "$lt": daterange[1]}, "courseid": courseid}},
            {"$project": {"username": "$username", "result": "$result"}},
            {"$unwind": "$username"},
            {"$group": {"_id": "$username", "submissions": {"$sum": 1}, "validSubmissions":
                {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}}}
             },
            {"$sort": {"submissions": -1}}])

        return [
            {"name": x["_id"],
             "submissions": x["submissions"],
             "validSubmissions": x["validSubmissions"]}
            for x in stats_users
        ]

    def _graph_stats(self, courseid, daterange):
        project = {
            "year": {"$year": "$submitted_on"},
            "month": {"$month": "$submitted_on"},
            "day": {"$dayOfMonth": "$submitted_on"},
            "result": "$result"
        }
        groupby = {"year": "$year", "month": "$month", "day": "$day"}

        method = "day"
        if (daterange[1] - daterange[0]).days < 7:
            project["hour"] = {"$hour": "$submitted_on"}
            groupby["hour"] = "$hour"
            method = "hour"

        min_date = daterange[0].replace(minute=0, second=0, microsecond=0)
        max_date = daterange[1].replace(minute=0, second=0, microsecond=0)
        delta1 = timedelta(hours=1)
        if method == "day":
            min_date = min_date.replace(hour=0)
            max_date = max_date.replace(hour=0)
            delta1 = timedelta(days=1)

        stats_graph = self.database.submissions.aggregate(
            [{"$match": {"submitted_on": {"$gte": min_date, "$lt": max_date+delta1}, "courseid": courseid}},
             {"$project": project},
             {"$group": {"_id": groupby, "submissions": {"$sum": 1}, "validSubmissions":
                 {"$sum": {"$cond": {"if": {"$eq": ["$result", "success"]}, "then": 1, "else": 0}}}}
              },
             {"$sort": {"_id": 1}}])

        increment = timedelta(days=(1 if method == "day" else 0), hours=(0 if method == "day" else 1))

        all_submissions = {}
        valid_submissions = {}

        cur = min_date
        while cur <= max_date:
            all_submissions[cur] = 0
            valid_submissions[cur] = 0
            cur += increment

        for entry in stats_graph:
            c = datetime(entry["_id"]["year"], entry["_id"]["month"], entry["_id"]["day"], 0 if method == "day" else entry["_id"]["hour"])
            all_submissions[c] += entry["submissions"]
            valid_submissions[c] += entry["validSubmissions"]

        all_submissions = sorted(all_submissions.items())
        valid_submissions = sorted(valid_submissions.items())
        return (all_submissions, valid_submissions)

    def GET_AUTH(self, courseid, f=None, t=None, diag=None):  # pylint: disable=arguments-differ
        """ GET request """

        def _clean_data(data):
            """ tools method to clean data from request """
            cleaned = data.replace("&#39;", "")
            cleaned = cleaned.replace("[", "")
            cleaned = cleaned.replace("]", "")
            cleaned = cleaned.replace(" ", "")
            cleaned = cleaned.split(",")
            return cleaned

        def _per_question_diagram_compilation():
            dicgrade = {}
            data = web.input()
            student_ids = _clean_data(data["student_ids"])
            task_ids = _clean_data(data["task_ids"])
            evaluated_submissions = {}
            for task_id in task_ids:
                evaluated_submissions[task_id] = []

            def students_per_grade(grades_per_tasks):
                for key, value in grades_per_tasks.items():
                    dicgrade[key] = {}
                    for grade in value:
                        grade = float(grade) / 5
                        grade = round(grade * 2) * 0.5
                        if grade not in dicgrade[key]:
                            dicgrade[key][grade] = 1
                        else:
                            dicgrade[key][grade] = dicgrade[key][grade] + 1
                return dicgrade

            if student_ids == ['']:
                student_ids = (self.database.aggregations.find_one({"courseid": courseid}, {"students": 1}))
                student_ids = student_ids["students"]

            subs = list(self.database.submissions.aggregate(
                [
                    {
                        "$match": {"$and": [
                            {"taskid": {"$in": task_ids}, "username": {"$in": student_ids}, "courseid": courseid}]}
                    },
                    {
                        "$group":
                            {
                                "_id": {
                                    "username": "$username",
                                    "taskid": "$taskid",
                                    "courseid": "$courseid"
                                },
                                "grade": {"$last": "$grade"},
                                "submitted_on": {"$last": "$submitted_on"}
                            }
                    }
                ]
            ))
            for sub in subs:
                evaluated_submissions[sub["_id"]["taskid"]].append(sub["grade"])

            table_stud_per_grade = students_per_grade(evaluated_submissions)
            task_titles = {}
            for task_id in tasks:
                task_titles[task_id] = tasks[task_id].get_name(self.user_manager.session_language())

            data = {}
            data["stud_per_grad"] = table_stud_per_grade
            data["task_titles"] = task_titles
            return json.dumps(data)

        def _per_status_diagram_compilation():
            course = self.course_factory.get_course(courseid)
            data = web.input()
            task_ids = _clean_data(data["task_ids"])
            tasks_data = {}
            tasks_data["nstuds"] = len(self.user_manager.get_course_registered_users(course, False))
            for task_id in task_ids:
                data = list(self.database.user_tasks.aggregate(
                    [
                        {
                            "$match":
                                {
                                    "courseid": courseid,
                                    "taskid": task_id,
                                    "username": {"$in": self.user_manager.get_course_registered_users(course, False)}
                                }
                        },
                        {
                            "$group":
                                {
                                    "_id": "$taskid",
                                    "viewed": {"$sum": 1},
                                    "attempted": {"$sum": {"$cond": [{"$ne": ["$tried", 0]}, 1, 0]}},
                                    "succeeded": {"$sum": {"$cond": ["$succeeded", 1, 0]}}
                                }
                        }
                    ]))
                tasks_data[task_id] = data
            task_titles = []
            for task_id in tasks:
                task_titles.append(tasks[task_id].get_name(self.user_manager.session_language()))
            data = {}
            data["stud_per_grad"] = tasks_data
            data["task_titles"] = task_titles
            return json.dumps(data)

        course, __ = self.get_course_and_check_rights(courseid)
        tasks = course.get_tasks()
        now = datetime.now().replace(minute=0, second=0, microsecond=0)

        error = None
        if diag == "diag1":
            return _per_question_diagram_compilation()
        if diag == "diag2":
            return _per_status_diagram_compilation()
        if f == None and t == None:
            daterange = [now - timedelta(days=14), now]
        else:
            try:
                daterange = [datetime.strptime(x[0:16], "%Y-%m-%dT%H:%M") for x in (f,t)]
            except:
                error = "Invalid dates"
                daterange = [now - timedelta(days=14), now]

        stats_tasks = self._tasks_stats(courseid, tasks, daterange)
        stats_users = self._users_stats(courseid, daterange)
        stats_graph = self._graph_stats(courseid, daterange)
        tasks, user_data, aggregations, tutored_aggregations, \
        tutored_users, checked_tasks, checked_users, show_aggregations = self.show_page_params(course, web.input())
        return self.template_helper.get_renderer().course_admin.stats(course, stats_graph, stats_tasks, stats_users,
                                                                      daterange, error, tasks,user_data,aggregations,
                                                                      tutored_aggregations,tutored_users,checked_tasks,
                                                                      checked_users,show_aggregations)


def compute_statistics(tasks, data, ponderation):
    """ 
    Compute statistics about submissions and tags.
    This function returns a tuple of lists following the format describe below:
    (   
        [('Number of submissions', 13), ('Evaluation submissions', 2), …], 
        [(<tag>, '61%', '50%'), (<tag>, '76%', '100%'), …]
    )
     """
    
    super_dict = {}
    for submission in data:
        task = tasks.get(submission["taskid"], None)
        if task:
            username = "".join(submission["username"])
            tags_of_course = [tag for key, tag in task.get_course().get_tags().items() if tag.get_type() in [0,1]]
            for tag in tags_of_course:
                super_dict.setdefault(tag, {})
                super_dict[tag].setdefault(username, {})
                super_dict[tag][username].setdefault(submission["taskid"], [0,0,0,0])
                super_dict[tag][username][submission["taskid"]][0] += 1
                if "tests" in submission and tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()]:
                    super_dict[tag][username][submission["taskid"]][1] += 1

                if submission["best"]:
                    super_dict[tag][username][submission["taskid"]][2] += 1
                    if "tests" in submission and tag.get_id() in submission["tests"] and submission["tests"][tag.get_id()]:
                        super_dict[tag][username][submission["taskid"]][3] += 1

    output = []
    for tag in super_dict:

        if not ponderation: 
            results = [0,0,0,0]
            for username in super_dict[tag]:
                for task in super_dict[tag][username]:
                    for i in range (0,4):
                        results[i] += super_dict[tag][username][task][i] 
            output.append((tag, 100*safe_div(results[1],results[0]), 100*safe_div(results[3],results[2])))


        #Ponderation by stud and tasks
        else:
            results = ([], [])
            for username in super_dict[tag]:
                for task in super_dict[tag][username]:
                    a = super_dict[tag][username][task]
                    results[0].append(safe_div(a[1],a[0]))
                    results[1].append(safe_div(a[3],a[2]))
            output.append((tag, 100*safe_div(sum(results[0]),len(results[0])), 100*safe_div(sum(results[1]),len(results[1]))))

    return (fast_stats(data), output)

def fast_stats(data):
    """ Compute base statistics about submissions """
    
    total_submission = len(data)
    total_submission_best = 0
    total_submission_best_succeeded = 0
        
    for submission in data:
        if "best" in submission and submission["best"]:
            total_submission_best = total_submission_best + 1
            if "result" in submission and submission["result"] == "success":
                total_submission_best_succeeded += 1
        
    statistics = [
        (_("Number of submissions"), total_submission),
        (_("Evaluation submissions (Total)"), total_submission_best),
        (_("Evaluation submissions (Succeeded)"), total_submission_best_succeeded),
        (_("Evaluation submissions (Failed)"), total_submission_best - total_submission_best_succeeded),
        # add here new common statistics
        ]
    
    return statistics
    
def safe_div(x,y):
    """ Safe division to avoid /0 errors """
    if y == 0:
        return 0
    return x / y