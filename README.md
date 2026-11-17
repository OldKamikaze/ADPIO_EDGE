# ADPIO EDGE - WEB-BASED IOT AUTOMATION PLATFORM FOR EDGE DEVICES

## [PROJECT'S WEBSITE: ADPIO EDGE](https://adpioedge.com)


Build around main fundamentals: 
1. Datapoints aggregation and integration
2. Flow based programming
3. GUI builder.
4. Data visualization, including trend engine

## Current Major Issues 
1. Linux only support, Windows support coming soon.
2. BACnet And MQTT - read only, write mode coming soon.

Dependencies for Python:
```
  python312 +
  uvicorn
  uvloop #optional
  fastapi
  ujson
  sqlmodel
  bacpypes3
  psutil #cpu and mem info
```


## Quick Start
Instructions on getting started:
1. `./start_adpio.sh` or `./start_adpio.sh debug`
2. Open <http://localhost:8000>
3. Login with default credentials admin/admin

More info and documents can be found at [ADPIO EDGE DOCUMENTATION](https://adpioedge.com/docs/install/run) 
   

