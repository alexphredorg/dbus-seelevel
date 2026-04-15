def box_volume(length, width, height):
    return length * width * height


def triangular_prism_volume(base_length, height, depth):
    triangle_area = 0.5 * base_length * height
    return triangle_area * depth


def cubic_inches_to_gallons(cubic_inches):
    GALLONS_PER_CUBIC_INCH = 0.004329
    return cubic_inches * GALLONS_PER_CUBIC_INCH

def cubic_inches_to_meters_cubed(cubic_inches):
    CUBIC_INCHES_PER_CUBIC_METER = 61023.7441
    return cubic_inches / CUBIC_INCHES_PER_CUBIC_METER

# This computes the volume of water in a Ronco B171 tank at a given height.
# returns cubic inches of water
def B171_tank_volume_at_height(water_height):
    tank_wall_thickness = 0.633
    #tank_wall_thickness = 0
    tank_width_top = 22 - tank_wall_thickness
    tank_width_bottom = 9 - tank_wall_thickness
    tank_height = 14
    tank_length = 24 - tank_wall_thickness
    tank_slope_height = 8

    assert water_height >= 0, "Water height must be non-negative"
    assert water_height <= tank_height, f"Water height must be less than or equal to {tank_height} inches"

    water_height_slope = tank_slope_height
    if water_height < tank_slope_height:
        water_height_slope = water_height

    # compute 3 volumes and add them
    # _____________
    # |    C      |
    # |___________|
    # |       |B /
    # |   A   | /
    # |_______|/
    # tank_volume_bottom_box = A
    # tank_volume_prism = B
    # tank_volume_upper_box = C

    tank_volume_bottom_box = box_volume(tank_length, tank_width_bottom, water_height_slope)
    slope = (tank_width_top - tank_width_bottom) / (tank_slope_height)
    prism_base_length = slope * water_height_slope
    tank_volume_prism = triangular_prism_volume(prism_base_length, water_height_slope, tank_length)
    tank_volume_upper_box = 0
    if water_height > tank_slope_height:
        tank_volume_upper_box = box_volume(tank_length, tank_width_top, water_height - tank_slope_height)
    #print(water_height, water_height_slope, tank_volume_bottom_box, tank_volume_prism, tank_volume_upper_box)
    tank_volume = tank_volume_bottom_box + tank_volume_prism + tank_volume_upper_box
    return tank_volume


if __name__ == "__main__":
    for height in range(0, 8):
        height = (height / 8) * 14 
        #height = height / 2
        volume_ci = B171_tank_volume_at_height(height)
        volume_gal = cubic_inches_to_gallons(volume_ci)
        percent_full = volume_gal / 25 * 100
        percent_height = height / 14 * 100
        print(f"Water height: {height} inches / {percent_height:.0f}%, Volume: {volume_ci:.2f} cubic inches, Volume: {volume_gal:.2f} gallons {percent_full:.2f}% full")

