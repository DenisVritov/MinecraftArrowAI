

import random

from util.grid_observer_parse import get_solid_y


def find_con_spawn(con_x, con_z, con, obs_map, obx, oby, x, y, z, tries=10, center=True):
    """
    This method will find a random, safe, spot to spawn within
    the observable area of the player, if possible. It will also 
    constrain the spawning to within a specified constraint from
    a given x, z coordinate.

    input:
        con_x (int) - The x coordiante that the new spawn will be constrained.

        con_z (int) - The z coordinate that the new spawn will be constrained.

        con (int) - The amount to constrain the x and z difference.

        obs_map (list) - map from grid['Map'] from a grid observation.

        obx (int) - The distance to the edge of the x axis
                    grid from the player. Ex. If the player
                    is in the center of a 51 meter cube
                    the obx will be 25.

        oby (int) - The observation distance from the player to the heighest
                    y point.

        x (int) - The x coordinate of the player.

        y (int) - The y coordinate of the player.

        z (int) - The z coordinate of the player.

        tries (int) - Number of attempts to try finding a spawning point until
                      giving up.

        center (bool) - If the returned spawn should be centered on the block.

    output:
        The x, y, z coordinates that can be used for the next spawn.
        If, after x tries (10 default) no spawn is found, return None.
    """ 
    nx = ny = nz = None
    while (nx is None or ny is None or nz is None or 
           abs(con_x-nx) > con or abs(con_z-nz) > con):
        nx, ny, nz = find_rand_spawn(obs_map, obx, oby, x, y, z, tries)
    print('Found new Spawn:', nx, ny, nz)
    return nx, ny, nz


def find_rand_spawn(obs_map, obx, oby, x, y, z, tries=10, center=True):
    """
    This method will find a random, safe, spot to spawn within
    the observable area of the player, if possible.

    input:
        obs_map (list) - map from grid['Map'] from a grid observation.

        obx (int) - The distance to the edge of the x axis
                    grid from the player. Ex. If the player
                    is in the center of a 51 meter cube
                    the obx will be 25.

        oby (int) - The observation distance from the player to the heighest
                    y point.

        x (int) - The x coordinate of the player.

        y (int) - The y coordinate of the player.

        z (int) - The z coordinate of the player.

        tries (int) - Number of attempts to try finding a spawning point until
                      giving up.

        center (bool) - If the returned spawn should be centered on the block.


    output:
        The x, y, z coordinates that can be used for the next spawn.
        If, after x tries (10 default) no spawn is found, return None.
    """
    rx = random.randint(-obx, obx)
    ry = None
    rz = random.randint(-obx, obx)
    ax = rx+obx
    az = rz+obx
    count = tries
    while count > 0:
        ry = get_solid_y(obs_map, obx, oby, ax, az)
        count -= 1
    if ry is None:
        return None, None, None
    if center:
        rx += -0.5 if rx < 0 else 0.5
        rz += -0.5 if rz < 0 else 0.5
    return x+rx, y+ry, z+rz
