

import math
import numpy as np
import skimage.draw as draw

from matplotlib import collections as mc
from matplotlib import pyplot as plt
from util.data_collection import save_data
from util.data_collection import save_labels
from util.grid_observer_parse import get_block


def find_yaw(xp, zp, xt, zt):
    """
    Determines the yaw between the player and the target.

    input:
        xp (int) - x coordinate of the player (0 if relative to
                   the player.)

        zp (int) - z coordinate of the player (0 if relative to
                   the player.)

        xt (int) - x coordinate of the target

        zt (int) - z coordinate of the target

    return:
        The angle that will cause the player to face the
        target. In Minecraft due south is a yaw angle of 0.    
    """
    dx = xt-xp
    dz = zt-zp
    return -180 * math.atan2(dx, dz) / math.pi


def check_hit_ob(x_arr, h_arr, dist, ob_b, ob_h=1, constrain=True):
    """
    Check if the arrow hit a single obstacle.

    input:
        x_arr (list) - The x position of the arrow from
                       the player.

        h_arr (list) - The height of the arrow compared
                       to the block the player is standing
                       upon.

        dist (int) - Distance of the target from the player.

        ob_b (int) - The height of the base of the target compared
                    to the block the player is standing upon.
                    Essentially the y coordinate relative to the
                    player.

        ob_h (int) - The height of the target from it's base to its top.

        constrained (bool) - If a small amount of size should be removed from the
                             top and bottom of the target so only shots more centered
                             will register as hits.

    return:
        A boolean that is True if the target was hit and
        False if the target was missed.
    """
    if len(h_arr) == 1:
        return False
    p1_t = (dist, ob_b + 0.25) if constrain else (dist, ob_b)
    p2_t = (dist, ob_b + ob_h - 0.15) if constrain else (dist, ob_b + ob_h)
    p1_arr = (x_arr[-2], h_arr[-2])
    p2_arr = (x_arr[-1], h_arr[-1])
    return intersect(p1_arr, p2_arr, p1_t, p2_t)


def check_hit_obs(x_arr, h_arr, obs):
    """
    Check if the arrow has hit an obstacle in a list of obstacles. This 
    functions makes sure that an arrow will not get stuck on an obstacle
    by making the arrow trajectory go over the obstacle by half of a block.

    input:
        x_arr (list) - The x position of the arrow from
                       the player.

        h_arr (list) - The height of the arrow compared
                       to the block the player is standing
                       upon.

        obs [[(dist, base), (dist, height)]]
                - A list of lists, where each element list
                  is a pair of points that draw a line segment
                  that's the obstacle. The first point is the 
                  distance of the obstacle and the base of the
                  obstacle. The second point is the distance of the
                  obstacle and the objects maximum height.

    output:
        A boolean that's True if the arrow intersects any of the obstacles
        and False otherwise.
    """
    if obs is None:
        return False
    p1_arr = (x_arr[-2], h_arr[-2])
    p2_arr = (x_arr[-1], h_arr[-1])
    for ob in obs:
        p1_ob = ob[0]
        p2_ob = list(ob[1])
        p2_ob[1] = p2_ob[1]+0.5
        if intersect(p1_arr, p2_arr, p1_ob, p2_ob):
            return True
    return False


def save_trajectory_info(x_arr, h_arr, t_d, t_b, t_h, obs=None, view_x=25, view_y=10):
    """
    Save a 2d line graph of the trajectory of an arrow as it travels from the 
    player to the target...hopefully that target that is...

    inputs:
        x_arr [float] - A list of float values that are the distance of the arrow
                        relative to the player.

        h_arr [float] - A list of float values that are the height of the arrow
                        relative to the player's height.

        t_d (float) - Distance of the target relative to the player.

        t_b (float) - The base of the target relative to the player's y position.

        t_h (float) - The height of the target from the base of the target.

        obs [[(dist, base), (dist, height)]]
                - A list of lists, where each element list
                  is a pair of points that draw a line segment
                  that's the obstacle. The first point is the 
                  distance of the obstacle and the base of the
                  obstacle. The second point is the distance of the
                  obstacle and its height from the base.

        view_x (int) - How many blocks in the 'x' direction of the graph.

        view_y (int) - How many blocks in the positive and negative y axis to be shown.

    """
    x_control = range(-1, int(math.sqrt(view_x**2 + view_y**2)) + 1)
    y_control = [0 for x in x_control]
    fig, ax = plt.subplots()
    ax.plot(x_control, y_control, linewidth=2, label='Player Standing')
    ax.plot(x_arr, h_arr, linewidth=2, color='b', label='Arrow Trajectory')
    if obs is not None:
            obs_col = mc.LineCollection(obs, color='r', label='Obstacles')
            ax.add_collection(obs_col)
    tar_col = mc.LineCollection([[(t_d, t_b), (t_d, t_b + t_h)]], color='g', label='Target')
    ax.add_collection(tar_col)
    ax.set_ylim([-view_y, view_y])
    ax.set_xlim([-1, math.sqrt(view_x**2 + view_x**2)])
    plt.title('Trajectory with Obstacles')
    plt.ylabel('Height (Relative to Player)')
    plt.xlabel('Distance (Relative to Player)')
    plt.legend()
    plt.savefig('graphs/trajectory_with_obs.png')


def sim_shot(angle, v_o, t_d, t_b, t_h, obs=None, image=False):
    """
    Simulate an arrow shot with the provided attributes. Then return how
    far the arrow missed the target. 

    input:
        angle (int) - The angle the arrow should be shot. Measuring 0 from
                      the horizon and positive in the intuitive 'up' direction.

        v_o (float) - Initial velocity.

        t_d (float) - Distance of the target relative to the player.

        t_b (float) - The base of the target relative to the player's y position.

        t_h (float) - The height of the target from the base of the target.

        obs [[(dist, base), (dist, height)]]
                - A list of lists, where each element list
                  is a pair of points that draw a line segment
                  that's the obstacle. The first point is the 
                  distance of the obstacle and the base of the
                  obstacle. The second point is the distance of the
                  obstacle and its height from the base.

        image (bool) - If trajectory information of the arrow should be saved.

    output:
        If the arrow missed the target the distance from the center of the target to
        the arrow's final position is returned.

        If the arrow hit the target 0 is returned.

    """
    x_arr = [0]
    h_arr = [1.62]
    v_x = [v_o * math.cos(math.radians(angle))]
    v_h = [v_o * math.sin(math.radians(angle))]

    while x_arr[-1] < t_d and v_x[-1] > .01:
        x_arr.append(x_arr[-1] + v_x[-1])
        h_arr.append(h_arr[-1] + v_h[-1])
        v_x.append(v_x[-1] * .99)
        v_h.append(v_h[-1] * .99 - .05)

        if check_hit_obs(x_arr, h_arr, obs):
            break

        if check_hit_ob(x_arr, h_arr, t_d, t_b, t_h): 
            if image:
                save_trajectory_info(x_arr, h_arr, t_d, t_b, t_h, obs=obs)
            return 0

    t_c = (t_b + t_h) / 2
    return math.sqrt((x_arr[-1] - t_d)**2 + (h_arr[-1] - t_c)**2)


def find_pitch(t_d, t_b, t_h=1, f=1, obs=None, image=False):
    """
    Find the pitch needed to hit a provided target. Remember,
    the arrow is shot from 1.62 meters from the y coordinate
    of the player. The initial velocity (v_o), drag and
    gravitational constant are all provided by Minecraft for 
    an arrow.

    input:
        t_d (int) - The distance of the target from the player.

        t_b (int) - The height of the base of the target compared
                    to the block the player is standing upon.
                    Essentially the y coordinate relative to the
                    player.

        f (int) - The initial force of the arrow. This is
                  calculated by the amount of time the bow
                  should be drawn between 0 and 1. Where 1
                  is one second of draw time.

        obs [[(dist, base), (dist, height)]]
                - A list of lists, where each element list
                  is a pair of points that draw a line segment
                  that's the obstacle. The first point is the 
                  distance of the obstacle and the base of the
                  obstacle. The second point is the distance of the
                  obstacle and its height from the base.

        image (bool) - If graphs should be created and saved based on 
                       arrow trajectory.

    output:
        The angle of the bow needed to hit the target via the given
        parameters. Remember, above the horizon the angle for the pitch
        is negative.
    """
    angle = -90
    v_o = (2 * f) + f**2
    while angle < 90:
        angle += 1
        dist = sim_shot(angle, v_o, t_d, t_b, t_h, obs, image=image)
        if dist == 0:
            return -1 * angle
    return None


def find_pow_pitch(dist, yt, obs=None, image=False):
    """
    Find the power (f) and pitch angle needed to hit a target given
    the provided parameters.

    input:
        dist (int) - The distance of the target from the player.

        yt (int) - The height of the base of the target compared
                   to the block the player is standing upon.
                   Essentially the y coordinate relative to the
                   player.

        obs [[(dist, base), (dist, height)]]
                - A list of lists, where each element list
                  is a pair of points that draw a line segment
                  that's the obstacle. The first point is the 
                  distance of the obstacle and the base of the
                  obstacle. The second point is the distance of the
                  obstacle and its height from the base.

    output:
        A tuple of power and pitch (f, pitch). The power (f) is the time 
        between 0 and 1 seconds to draw the bow to hit the target. The pitch
        is the angle the bow should be held to hit the target. Remember, in
        Minecraft the angle above the horizon is negative.
    """
    f_test = np.arange(1, 0, -0.1)
    for f in f_test:
        pitch = find_pitch(dist, yt, f=f, obs=obs, image=image)
        if pitch is not None:
            return f, pitch
    return None, None


def find_target_coords(obs_map, block, obx, oby, obz, apx, apy, apz, center=True):
    """
    This function takes the map from the coordinate observer
    and returns the target block's (x, y, z) with the player
    as the origin. This converts from the coordinate observers
    origin which is the top left hand corner (or 0 in map)
    position.
    This only works if the observed area is square.

    inputs:
        obs_map (list) - map from grid['Map'] from a grid
                         observation.

        block (str) - name of the block to target

        obx (int) - The distance to the edge of the x axis
                    grid from the player. Ex. If the player
                    is in the center of a 51 meter cube
                    the obx will be 25.

        oby (int) - The distance to the edge of the y axis
                    grid from the player. (See obx)

        obz (int) - The distance to the edge of the z axis
                    grid from the player. (See obx)

        apx (int) - Absolute x position of the player in Minecraft.

        apy (int) - Absolute x position of the player in Minecraft.

        apz (int) - Absolute x position of the player in Minecraft.

        center (bool) - If the target should be centered in
                        the block.

    return:
        A tuple as (x, y, z) with the coordinate of the target
        relative to the player.
    """
    if obx != obz:
        raise ValueError('Observed Map Area must be square!')
    try:
        pos = obs_map.index(block, 0)
    except:
        return (None, None, None)

    sx = obx*2+1
    sy = oby*2+1
    sz = obz*2+1
    rpx = sx//2
    rpy = sy//2
    rpz = sz//2
    tx = pos % (sx*sz) % sx
    ty = pos // (sx*sz)
    tz = pos % (sx*sz) // sz

    if center:
        tx += -0.5 if tx < 0 else 0.5
        tz += -0.5 if tz < 0 else 0.5
        pass
    return (tx-rpx-apx%1, ty-rpy-apy%1, tz-rpz-apz%1)


def obstacle_coords(obx, obz, tx, tz, image=False):
    """
    Determine the coordinates of all obstacles between the
    player and a specific point.

    input:
        obx (int) - The distance to the edge of the x axis
                    grid from the player. Ex. If the player
                    is in the center of a 51 meter cube
                    the obx will be 25.

        obz (int) - The distance to the edge of the z axis
                    grid from the player. (See obx)

        tx (int) - The x coordinate of the target relative to
                   the player.
 
        tz (int) - The y coordinate of the target relative to
                   the player.

    output:
        obs_coords ([[list x] [list z]]) - A list of two lists
                                           where the first is the x
                                           coords and the second is 
                                           the y coords. 
    """
    img = np.zeros([obx*2+1, obz*2+1])
    rr,cc, val = draw.line_aa(obz, obx, int(tz)+obz, int(tx)+obx)
    img[rr,cc] = val
    obs = np.nonzero(img)

    if image:
        plt.figure(0)
        plt.cla()
        plt.imshow(img, interpolation='nearest')
        plt.plot([obx, tx+obx], [obz, tz+obz], linewidth=2, color='r')
        plt.title('Player Vision (North up)')
        plt.ylabel('Z axis')
        plt.xlabel('X axis')
        plt.savefig('graphs/player_vision.png')

        plt.figure(1)
        plt.cla()
        plt.imshow(img, interpolation='nearest')
        plt.plot(obs[1], obs[0])
        plt.title('Obstacles Viewed (North up)')
        plt.ylabel('Z axis')
        plt.xlabel('X axis')
        plt.savefig('graphs/obstacles_viewed.png')

    return (obs[1], obs[0])


def get_obs(obs_map, obs_coords, oby, obx, target, image=False):
    """
    Determine the height and distance of all obstacles from the player.

    input:
        obs_map (list) - map from grid['Map'] from a grid
                         observation.

        obs_coords ([[list x] [list z]]) - A list of two lists
                                           where the first is the x
                                           coords and the second is 
                                           the y coords. 

        oby (int) - The observation distance from the player to the heighest
                    y point.

        obx (int) - The distance to the edge of the x axis
                    grid from the player. Ex. If the player
                    is in the center of a 51 meter cube
                    the obx will be 25.

        target (str) - The minecraft block id of our target block.

        image (bool) - Boolean if graphs should be created and saved
                       of the obstacles.

    output:
        obs [[(dist, base), (dist, height)]]
                - A list of lists, where each element list
                  is a pair of points that draw a line segment
                  that's the obstacle. The first point is the 
                  distance of the obstacle and the base of the
                  obstacle. The second point is the distance of the
                  obstacle and its height from the base.
    """
    obs = []
    for i in range(len(obs_coords[0])):
        x = obs_coords[0][i]
        z = obs_coords[1][i]
        for y in range(2*oby, 0, -1):
            block = get_block(obs_map, 2*obx+1, x, y, z)
            if block != 'air':  
                if block == target:
                    break  
                dist = math.sqrt((x-obx)**2 + (z-obx)**2)
                obs.append([(dist, -oby), (dist, y-oby+1)])
                break
    if image:
        x_control = range(-1, int(math.sqrt(obx**2+obx**2))+1)
        y_control = [0 for x in x_control]
        obs_col = mc.LineCollection(obs)

        fig, ax = plt.subplots()
        ax.plot(x_control, y_control, linewidth=2)
        ax.add_collection(obs_col)
        ax.set_ylim([-oby, oby])
        ax.set_xlim([-1, math.sqrt(obx**2+obx**2)])
        plt.title('Obstacles')
        plt.ylabel('Height')
        plt.xlabel('Distance from Player')
        plt.savefig('graphs/obstacles.png')
    return obs


def pitch_yaw_force(block, grid, obx, oby, obz, target, record=False, image=False):
    """
    Determine the pitch, yaw, and force needed to hit a specified block.
    The first block found while searching the grid_map will become the
    target.

    input:
        block (str) - The Minecraft id of the block to target.

        grid (dict) - The unpaked json response from a grid observation.

        obx (int) - The distance to the edge of the x axis
                    grid from the player. Ex. If the player
                    is in the center of a 51 meter cube
                    the obx will be 25.

        oby (int) - The distance to the edge of the y axis
                    grid from the player. (See obx)

        obz (int) - The distance to the edge of the z axis
                    grid from the player. (See obx)

        target (str) - The minecraft block id of our target block.

        record (bool) - A flag if the data (tx, ty, tz, obs) and labels
                        (pitch, yaw, force) should be recorded.

    output:
        A tuple of (pitch, yaw, force) needed to hit the first found 
        block in the obs_map.

    """
    print('Getting Target Coords')
    px, py, pz = grid['XPos'], grid['YPos'], grid['ZPos']
    tx, ty, tz = find_target_coords(grid['Map'], block, obx, oby, obz, px, py, pz)
    print('Tx:', tx, 'Ty:', ty, 'Tz:', tz)

    if tx is None or ty is None or tz is None:
        return None, None, None

    print('Determining Obstacles')
    obs_coords = obstacle_coords(obx, obz, tx, tz, image=image)
    obs = get_obs(grid['Map'], obs_coords, oby, obx, target, image=image)

    print('Determining Power, Yaw and Pitch')
    yaw = find_yaw(0, 0, tx, tz)
    dist = math.sqrt(tx**2 + tz**2)
    f, pitch = find_pow_pitch(dist, ty, obs, image=image)
    print('pitch: ', pitch, 'yaw:', yaw, 'f:', f)

    if record:
        save_data(tx, ty, tz, obs)
        save_labels(pitch, yaw, f)

    return pitch, yaw, f


def intersect(A,B,C,D):
    """
    Return true if line segments AB and CD intersect. This function
    was provided in the following stackoverflow comment.

    https://stackoverflow.com/
    questions/3838329/how-can-i-check-if-two-segments-intersect
    """
    return (ccw(A,C,D) != ccw(B,C,D)) and (ccw(A,B,C) != ccw(A,B,D))


def ccw(A,B,C):
    """
    From the below stackoverflow comment.

    https://stackoverflow.com/
    questions/3838329/how-can-i-check-if-two-segments-intersect
    """
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
