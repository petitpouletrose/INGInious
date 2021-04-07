broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost'
broker_transport_options = {'visibility_timeout': 3600}  # 1 hour.
timezone = 'Europe/Brussels'
enable_utc = True