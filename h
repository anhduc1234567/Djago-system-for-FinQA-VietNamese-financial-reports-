[0;1;31m●[0m mongodb.service - High-performance, schema-free document-oriented >database
     Loaded: loaded (/etc/systemd/system/mongodb.service; enabled; vendor preset: enabled)
     Active: [0;1;31mfailed[0m (Result: exit-code) since Wed 2025-11-05 15:25:43 +07; 16s ago
    Process: 3849000 ExecStart=/usr/bin/mongod --quiet --config /etc/mongod.conf [0;1;31m(code=exited, status=1/FAILURE)[0m
   Main PID: 3849000 (code=exited, status=1/FAILURE)

Thg 11 05 15:25:43 nmtuet-serv systemd[1]: Started High-performance, schema-free document-oriented >database.
Thg 11 05 15:25:43 nmtuet-serv mongod[3849000]: {"t":{"$date":"2025-11-05T08:25:43.923Z"},"s":"F",  "c":"CONTROL",  "id":20574,   "ctx":"main","msg":"Error during global initialization","attr":{"error":{"code":38,"codeName":"FileNotOpen","errmsg":"Failed to open /var/log/mongodb/mongod.log"}}}
Thg 11 05 15:25:43 nmtuet-serv systemd[1]: [0;1;39m[0;1;31m[0;1;39mmongodb.service: Main process exited, code=exited, status=1/FAILURE[0m
Thg 11 05 15:25:43 nmtuet-serv systemd[1]: [0;1;38;5;185m[0;1;39m[0;1;38;5;185mmongodb.service: Failed with result 'exit-code'.[0m
