try:
    from malmo import MalmoPython
except:
    import MalmoPython

import os
import sys
import time
import json
import random
import numpy as np
from priority_dict import priorityDictionary as PQ


class MineExpressBaseline():
    def __init__(self):  
        # Static Parameters
        self.size = 8
        self.up_down_dist = self.size*4+5
        self.grid = []
        self.start = -1
        self.end = -1
        self.action_dict = {
            0: 'movenorth 1',
            1: 'movesouth 1',
            2: 'moveeast 1',
            3: 'movewest 1'
        }
        self.block_dict = {
            "base": 'diamond_ore',
            "slower1": 'packed_ice',
            "slower2": 'soul_sand', 
            "start": 'emerald_block',
            "end": 'redstone_block'
        }
        
        
    def find_start_end(self):
        for i in range(len(self.grid)):
            if self.grid[i] == self.block_dict["start"]:
                self.start = i
            elif self.grid[i] == self.block_dict["end"]:
                self.end = i
        
        
    def extract_action_list_from_path(self, path_list):
        action_trans = {-self.up_down_dist: 'movenorth 1', self.up_down_dist: 'movesouth 1', -1: 'movewest 1', 1: 'moveeast 1'}
        alist = []
        for i in range(len(path_list) - 1):
            curr_block, next_block = path_list[i:(i + 2)]
            alist.append(action_trans[next_block - curr_block])
        
        return alist
        
        
    def dijkstra_shortest_path(self):
        pre_grids = PQ()
        grid_dist = PQ()
        grid_dist[self.start] = 0
        pre_grids[self.start] = -1
        while grid_dist:
            cur = grid_dist.smallest()
            for g in [-self.up_down_dist,self.up_down_dist,-1,1]:
                g+=cur
                if g not in pre_grids and self.grid[g] != "air":
                    if g not in grid_dist or grid_dist[g] > grid_dist[cur]+1:
                        grid_dist[g] = grid_dist[cur]+1
                        pre_grids[g] = cur
            del grid_dist[cur]
        result = []
        cur = self.end
        while pre_grids[cur] != -1:
            result.insert(0,cur)
            cur = pre_grids[cur]
        result.insert(0,self.start)
        return result
        
    def run(self, world_state):
        while world_state.is_mission_running:
            #sys.stdout.write(".")
            time.sleep(0.1)
            world_state = agent_host.getWorldState()
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')
        
            if world_state.number_of_observations_since_last_state > 0:
                msg = world_state.observations[-1].text
                observations = json.loads(msg)
                self.grid = observations.get(u'floorAll', 0)
                break
            
        self.find_start_end()
        print("Output (start,end)", (i+1), ":", (self.start,self.end))
        path = self.dijkstra_shortest_path()
        print("Output (path length)", (i+1), ":", len(path))
        action_list = self.extract_action_list_from_path(path)
        
        return action_list
        

def GetMissionXML(size=8):
    map = np.zeros((16, 16))
        
    for i in range(0, 16, 3):
        map[i] = np.ones(16)
        map[:, i] = np.ones(16)
        
        for j in range(1, 14, 3):
            map[i, j:j + 2] = list(np.random.binomial(1, 0.25, 1) + 1) * 2
            map[j:j + 2, i] = list(np.random.binomial(1, 0.25, 1) + 1) * 2
    
    spawnPoint = np.random.randint(0, 7, 2)
    while (map[spawnPoint[0], spawnPoint[1]] == 0):
        spawnPoint = np.random.randint(0, 7, 2)
    
    endPoint = np.random.randint(8, 15, 2)
    while (map[endPoint[0], endPoint[1]] == 0):
        endPoint = np.random.randint(8, 15, 2)
    
    mapXML = ""
    
    for x in range(size, -size, -1):
        for y in range(size, -size, -1):
            
            if map[x + size - 1][y + size - 1] == 0:
                mapXML += f"<DrawBlock x='{x}'  y='10' z='{y}' type='air' />"
            
            elif x + size - 1 == spawnPoint[0] and y + size - 1 == spawnPoint[1]:
                mapXML += f"<DrawBlock x='{x}'  y='10' z='{y}' type='emerald_block' />"
            elif x + size - 1 == endPoint[0] and y + size - 1 == endPoint[1]:
                mapXML += f"<DrawBlock x='{x}'  y='10' z='{y}' type='redstone_block' />"
            
            elif map[x + size - 1][y + size - 1] == 1:
                mapXML += f"<DrawBlock x='{x}'  y='10' z='{y}' type='diamond_block' />"
            
            elif map[x + size - 1][y + size - 1] == 2:
                mapXML += f"<DrawBlock x='{x}'  y='10' z='{y}' type='soul_sand' />"

    return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
            <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

              <About>
                <Summary>Herobrine Project</Summary>
              </About>

            <ServerSection>
              <ServerInitialConditions>
                <Time>
                    <StartTime>3000</StartTime>
                    <AllowPassageOfTime>false</AllowPassageOfTime>
                </Time>
                <Weather>clear</Weather>
              </ServerInitialConditions>
              <ServerHandlers>
                  <FlatWorldGenerator generatorString="3;7,11;1;"/>
                  <DrawingDecorator>''' + \
                      "<DrawCuboid x1='{}' x2='{}' y1='2' y2='11' z1='{}' z2='{}' type='air'/>".format(-size, size, -size, size) + \
                      mapXML + \
                      '''
                  </DrawingDecorator>
                  <ServerQuitFromTimeUp timeLimitMs="10000"/>
                  <ServerQuitWhenAnyAgentFinishes/>
                </ServerHandlers>
              </ServerSection>

              <AgentSection mode="Survival">
                <Name>Mineclient</Name>
                <AgentStart>''' + \
                    "<Placement x='{}' y='11' z='{}' yaw='0'/>".format(spawnPoint[0]-size+1.5,spawnPoint[1]-size+1.5) + \
                    '''
                </AgentStart>
                <AgentHandlers>
                    <DiscreteMovementCommands/>
                    <AgentQuitFromTouchingBlockType>
                        <Block type="redstone_block"/>
                    </AgentQuitFromTouchingBlockType>
                    <ObservationFromGrid>
                      <Grid name="floorAll"> ''' + \
                        "<min x='{}' y='-1' z='{}'/>".format(-size*2-2,-size*2-2) + \
                        "<max x='{}' y='-1' z='{}'/>".format(size*2+2,size*2+2) + \
                      '''  
                      </Grid>
                  </ObservationFromGrid>
                </AgentHandlers>
              </AgentSection>
            </Mission>'''



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

if agent_host.receivedArgument("test"):
    num_repeats = 1
else:
    num_repeats = 1

for i in range(num_repeats):
    my_mission = MalmoPython.MissionSpec(GetMissionXML(), True)
    my_mission_record = MalmoPython.MissionRecordSpec()
    my_mission.requestVideo(800, 500)
    my_mission.setViewpoint(1)
    # Attempt to start a mission:
    max_retries = 3
    my_clients = MalmoPython.ClientPool()
    my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

    for retry in range(max_retries):
        try:
            agent_host.startMission( my_mission, my_clients, my_mission_record, 0, "%s-%d" % ('Moshe', i) )
            break
        except RuntimeError as e:
            if retry == max_retries - 1:
                print("Error starting mission", (i+1), ":",e)
                exit(1)
            else:
                time.sleep(2)

    # Loop until mission starts:
    print("Waiting for the mission", (i+1), "to start ",)
    world_state = agent_host.getWorldState()
    while not world_state.has_mission_begun:
        time.sleep(0.1)
        world_state = agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:",error.text)

    print()
    print("Mission", (i+1), "running.")

    agent = MineExpressBaseline()
    action_list = agent.run(world_state)

    print("Output (actions)", (i+1), ":", action_list)
    # Loop until mission ends:
    action_index = 0
    while world_state.is_mission_running:
        #sys.stdout.write(".")
        time.sleep(0.1)

        # Sending the next commend from the action list -- found using the Dijkstra algo.
        if action_index >= len(action_list):
            print("Error:", "out of actions, but mission has not ended!")
            time.sleep(2)
        else:
            agent_host.sendCommand(action_list[action_index])
        action_index += 1
        if len(action_list) == action_index:
            # Need to wait few seconds to let the world state realise I'm in end block.
            # Another option could be just to add no move actions -- I thought sleep is more elegant.
            time.sleep(2)
        world_state = agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:",error.text)

    print()
    print("Mission", (i+1), "ended")
    # Mission has ended.