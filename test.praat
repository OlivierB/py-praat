form Server
    sentence Address localhost
    natural Port 10000
endform

val=50

#writeInfoLine(address$)
#do ("sendsocket", "localhost:10000", "INF")
sendsocket 'address$':'port' INF 'val'
#sendsocket localhost:port (serv_port) INF val