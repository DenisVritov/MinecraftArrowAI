
def get_block(obs_map, s, ax, ay, az):
    """
    Determine the specific block at the given x, y, z. These coordinates
    are the absolute coordinates of the obs_map where the top left of an
    xz grid is 0, 0. Remember the xz grid must be square.

    input:
        obs_map (list) - map from grid['Map'] from a grid observation.

        s (int) - The size of one side of an xz grid. This is 2*obx+1,
                  where obx is the observation distance of the x 
                  coordinate. The obx should be equivilant to obz as this
                  will only work with a square grib.

        ax (int) - The absolute x coordinate of the block to check.

        ay (int) - The absolute y coordinate of the block to check.

        az (int) - The absolute z coordinate of the block to check.

    output:
        block_id (string) - The id of the block at the absolute 
                            coordinates given.
    """
    if ax < 0 or ay < 0 or az < 0:
        raise ValueError("Absolute Coords cannot be negative! Did you "
                         "accidentally use relative coordinates?")
    pos = ay*(s**2)
    pos += ax
    pos += az*s
    return obs_map[pos]


def get_nonair_y(obs_map, obx, oby, ax, az):
    """
    Get the first non-air y coordinate using the absolute x and
    z coordinates. These coordinates are measured from the top left
    hand corner of the grid observert.

    input:
        obs_map (list) - map from grid['Map'] from a grid observation.

        obx (int) - The distance to the edge of the x axis
                    grid from the player. Ex. If the player
                    is in the center of a 51 meter cube
                    the obx will be 25.

        oby (int) - The observation distance from the player to the heighest
                    y point.

        x (int) - The absolute x coordinate of the block to check.

        z (int) - The absolute z coordinate of the block to check.

    output:
        An integer which is the relative y coordinate to the player.
        None otherwise.
    """   
    for ay in range(2*oby, 0, -1):
        block = get_block(obs_map, 2*obx+1, ax, ay, az)
        if block != 'air':       
            return ay-oby+1
    return None


def get_solid_y(obs_map, obx, oby, ax, az):
    """
    Get the first solid block y coordinate using the absolute x and
    z coordinates. These coordinates are measured from the top left
    hand corner of the grid observert.

    input:
        obs_map (list) - map from grid['Map'] from a grid observation.

        obx (int) - The distance to the edge of the x axis
                    grid from the player. Ex. If the player
                    is in the center of a 51 meter cube
                    the obx will be 25.

        oby (int) - The observation distance from the player to the heighest
                    y point.

        ax (int) - The absolute x coordinate of the block to check.

        az (int) - The absolute z coordinate of the block to check.

    output:
        An integer which is the relative y coordinate to the player.
        This will return None if there is not a suitable block.
    """   
    for ay in range(2*oby, 0, -1):
        block = get_block(obs_map, 2*obx+1, ax, ay, az)
        if block == 'water' or block == 'lava':
            return None
        if block != 'air':
            return ay-oby+1
    return None
