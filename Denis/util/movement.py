
import math

from past.utils import old_div

def point_to(agent_host, ob, target_pitch, target_yaw, threshold):
    """
    Steer towards the target pitch/yaw, return True when 
    within the given tolerance threshold. This function is
    from the python_examples provided by Mojang.

    input:
        agent_host (agent_host) - The agent_host object for the 
                                  given player to control.

        ob (dict) - The observation json object parsed as a
                    dictionary. This can be any observation
                    object as long as the pitch and yaw are
                    provided.

        target_pitch (int) - The pitch for the agent to point.
                             Remember, in Minecraft down is positive
                             and up is negative.

        target_yaw (int) - The yaw for the agent to point.
                           Remember, in Minecraft south is 0.

        threshold (int) - How far from the target_pitch and 
                          target_yaw the agent may look before
                          returning true.

    return:
        True when the agent is within the tolerance of the
        target pitch and threshold
    """
    pitch = ob.get(u'Pitch', 0)
    yaw = ob.get(u'Yaw', 0)
    delta_yaw = angvel(target_yaw, yaw, 50.0)
    delta_pitch = angvel(target_pitch, pitch, 50.0)
    agent_host.sendCommand("turn " + str(delta_yaw))    
    agent_host.sendCommand("pitch " + str(delta_pitch))
    if abs(pitch-target_pitch) + abs(yaw-target_yaw) < threshold:
        agent_host.sendCommand("turn 0")
        agent_host.sendCommand("pitch 0")
        return True
    return False


def angvel(target, current, scale):
    """
    Use sigmoid function to choose a delta that will help 
    smoothly steer from current angle to target angle. This
    function was provided in the python examples by Mojang.
    """
    delta = target - current
    while delta < -180:
        delta += 360;
    while delta > 180:
        delta -= 360;
    return (old_div(2.0, (1.0 + math.exp(old_div(-delta,scale))))) - 1.0
