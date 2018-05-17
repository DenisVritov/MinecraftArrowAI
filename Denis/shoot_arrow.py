from __future__ import print_function
# ------------------------------------------------------------------------------------------------
# Copyright (c) 2016 Microsoft Corporation
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------

# Tutorial sample #1: Run simple mission

from builtins import range
from past.utils import old_div
from util.movement import point_to
from util.targeting import find_target_coords
from util.targeting import target_yaw_obs
from util.targeting import sim_shot
from util.spawning import find_con_spawn
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
import pandas as pd

import MalmoPython
import os
import sys
import time
import random
import math
import json
import numpy as np

if sys.version_info[0] == 2:
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately
else:
    import functools
    print = functools.partial(print, flush=True)

# Mission XML
def get_mission_xml(x, y, z, obx, oby, obz):
    print('GETTING MISSION XML')
    return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
            <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            
              <About>
                <Summary>Automatically shoot the diamond block!</Summary>
              </About>
              
              <ServerSection>
                <ServerInitialConditions>
                    <Weather>clear</Weather>
                    <Time>
                        <StartTime>1000</StartTime>
                        <AllowPassageOfTime>false</AllowPassageOfTime>
                    </Time>
                </ServerInitialConditions>

                <ServerHandlers>
                    <DefaultWorldGenerator seed="2"/>
                    <DrawingDecorator>
                        <DrawLine x1="235" y1="78" z1="315" x2="235" y2="79" z2="315" type="redstone_block"/>
                        <DrawBlock x="235" y="80" z="315" type="diamond_block"/>
                    
                        <DrawLine x1="235" y1="77" z1="346" x2="235" y2="78" z2="346" type="redstone_block"/>
                        <DrawBlock x="235" y="79" z="346" type="diamond_block"/>

                    </DrawingDecorator>
                    <ServerQuitFromTimeUp timeLimitMs="7000"/>
                    <ServerQuitWhenAnyAgentFinishes/>
                </ServerHandlers>
              </ServerSection>
              
              <AgentSection mode="Survival">
                <Name>James Bond</Name>
                <AgentStart>
                    <Placement x="{}" y="{}" z="{}" yaw="0"/>
                    <Inventory>
                        <InventoryItem slot="0" type="bow"/>
                        <InventoryItem slot="1" type="arrow" quantity="64"/>
                    </Inventory>
                </AgentStart>
                <AgentHandlers>
                  <ObservationFromGrid>
                    <Grid name="Map">
                      <min x="-{}" y="-{}" z="-{}"/>
                      <max x="{}" y="{}" z="{}"/>
                    </Grid>
                  </ObservationFromGrid>
                  <ObservationFromFullStats/> 
                  <ContinuousMovementCommands turnSpeedDegs="180"/>
                </AgentHandlers>
              </AgentSection>
            </Mission>'''.format(x, y, z, obx, oby, obz, obx, oby, obz)


# Create default Malmo objects:
agent_host = MalmoPython.AgentHost()
try:
    agent_host.parse( sys.argv )
except RuntimeError as e:
    print('ERROR:',e)
    print(agent_host.getUsage())
    exit(1)
if agent_host.receivedArgument("help"):
    print(agent_host.getUsage())
    exit(0)

data_path = '1kdata/20k_data.csv'
label_path = '1kdata/20k_labels.csv'

data = pd.read_csv(data_path, low_memory=False)
label = pd.read_csv(label_path, low_memory=False)

headers = ['x', 'y', 'z']
num_objs = (data.shape[1] - 3) // 2

dists = []
heights = []
for i in range(num_objs):
    dists.append('dist_' + str(i))
    heights.append('height_' + str(i))
    headers.append('dist_' + str(i))
    headers.append('height_' + str(i))

data.columns = headers
data = data.replace(to_replace='None', value=0).astype('float')

h_col = data[heights].idxmax(axis=1)
h_ind = [data.columns.get_loc(c) for c in h_col]

data_mh_list = [data.iloc[i, [0, 1, 2, h_ind[i] - 1, h_ind[i]]].tolist() for i in range(len(h_ind))]
mh_headers = ['x', 'y', 'z', 'dist', 'height']
mh = pd.DataFrame(data_mh_list, columns=mh_headers)
mhl = label.join(mh)

cols = ['y', 'dist', 'height']
target_distance = pd.DataFrame(np.sqrt(np.square(mhl['x']) + np.square(mhl['z'])), columns=['target_distance'])
X = pd.concat([target_distance, mhl[cols]], axis=1)
y = mhl[['f', 'pitch']]

# X = X.head(500)
# y = y.head(500)

X_train, X_test, y_train, y_test = train_test_split(X,
                                                    y,
                                                    test_size=0.33,
                                                    random_state=42)

mlr = MLPRegressor(activation='logistic', tol=1e-6, solver='lbfgs', random_state=1, alpha=10,
                   hidden_layer_sizes=(70,))
mlr.fit(X_train, y_train)
print('Predictor Trained')


# Continually do the mission
hit_targets = 0
total_shots = 0
missed_distance = []
con_x = 235
con_y = 0
con_z = 315
obx = obz = 25
oby = 10
x = 243
y = 76
z = 323
image = False
if len(sys.argv) > 1:
    image = sys.argv[1].lower() == 'true'
while True:
    missionXML = get_mission_xml(x, y, z, obx, oby, obz)
    my_mission = MalmoPython.MissionSpec(missionXML, True)
    my_mission_record = MalmoPython.MissionRecordSpec()

    # Attempt to start a mission:
    max_retries = 3
    for retry in range(max_retries):
        try:
            agent_host.startMission( my_mission, my_mission_record )
            break
        except RuntimeError as e:
            if retry == max_retries - 1:
                print("Error starting mission:",e)
                exit(1)
            else:
                time.sleep(2)

    # Loop until mission starts:
    print("Waiting for the mission to start ", end=' ')
    world_state = agent_host.getWorldState()
    while not world_state.has_mission_begun:
        print(".", end="")
        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:",error.text)

    print()
    print("Mission running ", end=' ')

    # Loop until mission ends:
    count = 1
    grid = None
    while world_state.is_mission_running:
        if world_state.observations and grid is None:
            tar_block = 'diamond_block'
            obvsCube = world_state.observations[0].text
            grid = json.loads(obvsCube)
            ty, tx, tz, dist, yaw, obs = target_yaw_obs(tar_block, grid, obx, oby, obz, tar_block, record=False, image=image)
            x, y, z = find_con_spawn(con_x, con_z, obx, grid['Map'], obx, oby, x, y, z)
            obstacles = [ [x[0], x[1]] for x in [z[1] for z in obs]]
            obstacles = np.asarray(obstacles)
            tallest = np.argmax(obstacles, axis=0)
            tallest_obj = obstacles[tallest[1]]
            X = np.asarray([dist] + [ty] + [tallest_obj[0]] + [tallest_obj[1]]).reshape(1,-1)
            preds = mlr.predict(X)
            print(preds)
            f = preds[0][0]
            pitch = preds[0][1]
            if f > 1:
                f = 1
            v0 = (2*f) + (f)**2
            t_to_target = dist/(v0*math.cos(math.radians(-1*pitch)))
            arr_h = 1.62 + v0*math.sin(math.radians(-1*pitch))*t_to_target - 0.025*(t_to_target)**2
            print(ty,arr_h)
#            con_x, con_y, con_z = find_target_coords(grid_map, tar_block, obx, oby, obz)

        if world_state.number_of_observations_since_last_state > 0:
            obvsText = world_state.observations[-1].text
            data = json.loads(obvsText) # observation comes in as a JSON string...
            if point_to(agent_host, data, preds[0][1], yaw, 0.1) and count > 0: # pitch is not None and
                count -= 1

                agent_host.sendCommand('use 1')
                print('Shooting...')
                time.sleep(preds[0][0])
                print('Shot...')
                agent_host.sendCommand('use 0')

                dist_from_target = abs(ty+0.5-arr_h)
                total_shots += 1
                if dist_from_target <= 0.5:
                    print('Arrow hit target!')
                    hit_targets += 1
                else:
                    print('Arrow is ' + str(dist_from_target - 0.5) + ' from target')
                    missed_distance.append(dist_from_target - 0.5)
                print('Fraction of shots hit ' + str(hit_targets / total_shots))
                print('Average distance of missed shots ' + str(np.average(np.asarray(missed_distance))))
                print('Median distance of missed shots ' + str(np.median(np.asarray(missed_distance))))

        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:",error.text)

    print()
    print("Mission ended")

