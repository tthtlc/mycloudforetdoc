
spacectl  config set x_domain_id "domain-root"
spacectl  config show

if x_domain_id is set:
---
api_key: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzcGFjZW9uZS5pZGVudGl0eSIsInR5cCI6IlNZU1RFTV9UT0tFTiIsIm93biI6IlNZU1RFTSIsImRpZCI6ImRvbWFpbi1yb290IiwiYXVkIjoiYWRtaW5AZXhhbXBsZS5jb20iLCJqdGkiOiI3ZWJlMzhlMTk3N2UwNWY1OGYwY2I0NzhkMmRkM2NlMSIsImlhdCI6MTc2MzYxMjU3NywidmVyIjoiMi4wIn0.WvPJqJ_gV3AW4Z5BzJK4ysRhyFoMxWhBVzL1MdZAQKA4nxoDqRzjEB9p5W04K66ZIKC84rO1gcdmMAQ1UekYeYnXe9Wj159zU38TwPBTUn8kDimPeJe0EDFrUmnxMoZ5b4fADo7QrkRe6y5-73gLxlTVW60-SBH3r4l5eMokFbVoXPGwVjP43okKDGfE2DHUDpkoIiggd49Bumr1FQEBfsUTosW54a7_kXTw6YZbubj_5H65mnYD8lpkDNuuXEp1_q2zCkqOAG-rDRoPh5LgYABF56PQqJ5ibl6VbWZL0YmHeZlGQhPEjKidesp0XNvXS26FqldJ54sj00y4JeR6Cw
endpoint: https://console4-v2-api.example.com
endpoints:
  board: grpc://board:50051
  config: grpc://config:50051
  cost_analysis: grpc://cost-analysis:50051
  dashboard: grpc://dashboard:50051
  file_manager: grpc://file-manager:50051
  identity: grpc://identity:50051
  inventory: grpc://inventory:50051
  monitoring: grpc://monitoring:50051
  notification: grpc://notification:50051
  plugin: grpc://plugin:50051
  repository: grpc://repository:50051
  secret: grpc://secret:50051
  statistics: grpc://statistics:50051
x_domain_id: domain-root


spacectl list domain
 domain_id   | name   | state   | created_at
-------------+--------+---------+--------------------------
 domain-root | root   | ENABLED | 2025-11-20T04:22:57.288Z





spacectl  config set x_domain_id ""
spacectl list domain
 domain_id           | name      | state   | created_at
---------------------+-----------+---------+--------------------------
 domain-root         | root      | ENABLED | 2025-11-20T04:22:57.288Z
 domain-36ae3e8ea400 | spaceone  | ENABLED | 2025-11-20T04:46:22.308Z
 domain-24f4390be576 | spaceone1 | ENABLED | 2025-11-29T03:50:50.228Z


spacectl config show:

---
api_key: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzcGFjZW9uZS5pZGVudGl0eSIsInR5cCI6IlNZU1RFTV9UT0tFTiIsIm93biI6IlNZU1RFTSIsImRpZCI6ImRvbWFpbi1yb290IiwiYXVkIjoiYWRtaW5AZXhhbXBsZS5jb20iLCJqdGkiOiI3ZWJlMzhlMTk3N2UwNWY1OGYwY2I0NzhkMmRkM2NlMSIsImlhdCI6MTc2MzYxMjU3NywidmVyIjoiMi4wIn0.WvPJqJ_gV3AW4Z5BzJK4ysRhyFoMxWhBVzL1MdZAQKA4nxoDqRzjEB9p5W04K66ZIKC84rO1gcdmMAQ1UekYeYnXe9Wj159zU38TwPBTUn8kDimPeJe0EDFrUmnxMoZ5b4fADo7QrkRe6y5-73gLxlTVW60-SBH3r4l5eMokFbVoXPGwVjP43okKDGfE2DHUDpkoIiggd49Bumr1FQEBfsUTosW54a7_kXTw6YZbubj_5H65mnYD8lpkDNuuXEp1_q2zCkqOAG-rDRoPh5LgYABF56PQqJ5ibl6VbWZL0YmHeZlGQhPEjKidesp0XNvXS26FqldJ54sj00y4JeR6Cw
endpoint: https://console4-v2-api.example.com
endpoints:
  board: grpc://board:50051
  config: grpc://config:50051
  cost_analysis: grpc://cost-analysis:50051
  dashboard: grpc://dashboard:50051
  file_manager: grpc://file-manager:50051
  identity: grpc://identity:50051
  inventory: grpc://inventory:50051
  monitoring: grpc://monitoring:50051
  notification: grpc://notification:50051
  plugin: grpc://plugin:50051
  repository: grpc://repository:50051
  secret: grpc://secret:50051
  statistics: grpc://statistics:50051
x_domain_id: ''
