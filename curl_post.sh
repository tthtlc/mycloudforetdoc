##curl 'https://console4-v2-api.example.com/inventory/job/analyze' \

url="https://console4-v1-api.example.com/api/repository/v1/plugin/get-plugin-endpoint"

curl -ikv $url \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: en-US,en;q=0.9,ko;q=0.8,zh-CN;q=0.7,zh;q=0.6' \
  -H 'authorization: Bearer eyJhbGciOiJSUzI1NiJ9.eyJhdWQiOiJhZG1pbkBkb21haW4uY29tIiwiZGlkIjoiZG9tYWluLTM2YWUzZThlYTQwMCIsImV4cCI6MTc2NTQ1Mjc3MywiaWF0IjoxNzY1NDUwOTczLCJpc3MiOiJzcGFjZW9uZS5pZGVudGl0eSIsImp0aSI6ImNiNmU4ZGI2ZTRkMjljMjkyMDEyMzU0Y2UxZGI1ZmNkIiwib3duIjoiVVNFUiIsInJvbCI6IldPUktTUEFDRV9PV05FUiIsInR5cCI6IkFDQ0VTU19UT0tFTiIsInZlciI6IjIuMCIsIndpZCI6IndvcmtzcGFjZS0xMjYwMmFkYzZiYTcifQ.SBPS5iwp_I-Fg1qqxDd__rjmLfoOO-od1I2qBf22OAIs1neEVMUhIl3wmr1eQDY39VSdTxTxLs3-dyxBobpw9r3KTUIzo55NvBb67HXtuJgGaktHlH08yn3YoZCio2EPj2U5PeZnosijuGkfNHXIF7ktk3VjTJ0l0xY7rqVx2aZvx45-RGXCg28woKO3SoEyfQcQaXz2jSPo78mv2DiQ0Nk1bE8C3EVIpx2CHipEPcLi6EbgS457bm1ytqAcDSP_GUIRsly0LoO1rwdpjYwaV9_kul3jEqAshIVmjqyH81OeC-G_lRRljPnOSc0WegkDvqCdwmCXYeDFXEmBmpAyrg' \
  -H 'content-type: application/json' \
  -H 'origin: https://console4.example.com' \
  -H 'priority: u=1, i' \
  -H 'referer: https://console4.example.com/' \
  -H 'sec-ch-ua: "Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-site' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36' \
  --data-raw '{"plugin_id": "plugin-hello-world-go","version": "1.0"}'


exit

  --data-raw '{"query":{"filter":[{"k":"collector_id","v":["collector-7f246568ad76","collector-464c4b8d1d28","collector-19fdbeb01f8f"],"o":"in"},{"k":"status","v":["IN_PROGRESS"],"o":"in"}],"group_by":["collector_id"],"fields":{"job_status":{"operator":"push","fields":{"job_id":"job_id","total_tasks":"total_tasks","remained_tasks":"remained_tasks"}}}}}' \
  --insecure ;

exit
  --data-raw 
