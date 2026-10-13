import os
import sys

# Kiểm tra SUMO_HOME
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Vui lòng khai báo biến môi trường 'SUMO_HOME'")

import traci
import sumolib

print("SUMO version info:")
print(f"SUMO_HOME đang trỏ tới: {os.environ['SUMO_HOME']}")
print("Cài đặt TraCI và Sumolib thành công!")