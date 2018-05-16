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
from util.targeting import pitch_yaw_force
from util.targeting import point_to

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
                    <FlatWorldGenerator generatorString="3;minecraft:bedrock,2*minecraft:dirt,minecraft:grass;1;village"/>
                    <DrawingDecorator>
                        <DrawLine x1="0" y1="4" z1="0" x2="0" y2="5" z2="0" type="redstone_block"/>
                        <DrawBlock x="0" y="6" z="0" type="diamond_block"/>
                    </DrawingDecorator>
                    <ServerQuitFromTimeUp timeLimitMs="10000"/>
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

# Continually do the mission
while True:
    x = random.randint(-25, 25)
    y = 4
    z = random.randint(-25, 25)
    
    obx = obz = 25
    oby = 10

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
            grid_map = grid['Map']
            tar_pitch, tar_yaw, f = pitch_yaw_force(tar_block, grid_map, obx, oby, obz)

        if world_state.number_of_observations_since_last_state > 0:
            obvsText = world_state.observations[-1].text
            data = json.loads(obvsText) # observation comes in as a JSON string...
            if tar_pitch is not None and point_to(agent_host, data, tar_pitch, tar_yaw, 0.1) and count > 0:
                count -= 1
                agent_host.sendCommand('use 1')
                time.sleep(f)
                agent_host.sendCommand('use 0')

        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:",error.text)

    print()
    print("Mission ended")

