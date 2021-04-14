broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost'
broker_transport_options = {'visibility_timeout': 3600}  # 1 hour.
task_serializer = 'json'
accept_content = ['json']  # Ignore other content
result_serializer = 'json'
timezone = 'Europe/Brussels'
enable_utc = True
