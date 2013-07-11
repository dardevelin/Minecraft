import math
import model

WALKING_SPEED = 5
FLYING_SPEED = 15

GRAVITY = 20.0
MAX_JUMP_HEIGHT = 1.5 # About the height of a block.
# To derive the formula for calculating jump speed, first solve
#    v_t = v_0 + a * t
# for the time at which you achieve maximum height, where a is the acceleration
# due to gravity and v_t = 0. This gives:
#    t = - v_0 / a
# Use t and the desired MAX_JUMP_HEIGHT to solve for v_0 (jump speed) in
#    s = s_0 + v_0 * t + (a * t^2) / 2
JUMP_SPEED = math.sqrt(2 * GRAVITY * MAX_JUMP_HEIGHT)
TERMINAL_VELOCITY = 50

PLAYER_HEIGHT = 2


class Player(object):
    
    def __init__(self):
        
        # When flying gravity has no effect and speed is increased.
        self.flying = False
        
        # First element is rotation of the player in the x-z plane (ground
        # plane) measured from the z-axis down. The second is the rotation
        # angle from the ground plane up. Rotation is in degrees.
        #
        # The vertical plane rotation ranges from -90 (looking straight down) to
        # 90 (looking straight up). The horizontal rotation range is unbounded.
        self.rotation = (0, 0)
        
        # Strafing is moving lateral to the direction you are facing,
        # e.g. moving to the left or right while continuing to face forward.
        #
        # First element is -1 when moving forward, 1 when moving back, and 0
        # otherwise. The second element is -1 when moving left, 1 when moving
        # right, and 0 otherwise.
        self.strafe = [0, 0]

        # Current (x, y, z) position in the world, specified with floats. Note
        # that, perhaps unlike in math class, the y-axis is the vertical axis.
        self.position = (0, 0, 0)
        
        # A list of blocks the player can place. Hit num keys to cycle.
        self.inventory = [model.BRICK, model.GRASS, model.SAND]
        
        # The current block the user can place. Hit num keys to cycle.
        self.block = self.inventory[0]
        
        # Velocity in the y (upward) direction.
        self.dy = 0
        
        #Bool for jumping
        self.jumping = False
        
        #Bool for determining if the spacebar is being help
        self.jumped = False
    
    def collide(self, position, height, world):
            """ Checks to see if the player at the given `position` and `height`
            is colliding with any blocks in the world.
    
            Parameters
            ----------
            position : tuple of len 3
                The (x, y, z) position to check for collisions at.
            height : int or float
                The height of the player.
    
            Returns
            -------
            position : tuple of len 3
                The new position of the player taking into account collisions.
    
            """
            # How much overlap with a dimension of a surrounding block you need to
            # have to count as a collision. If 0, touching terrain at all counts as
            # a collision. If .49, you sink into the ground, as if walking through
            # tall grass. If >= .5, you'll fall through the ground.
            pad = 0.25
            p = list(position)
            np = model.normalize(position)
            for face in model.FACES:  # check all surrounding blocks
                for i in xrange(3):  # check each dimension independently
                    if not face[i]:
                        continue
                    # How much overlap you have with this dimension.
                    d = (p[i] - np[i]) * face[i]
                    if d < pad:
                        continue
                    for dy in xrange(height):  # check each height
                        op = list(np)
                        op[1] -= dy
                        op[i] += face[i]
                        if tuple(op) not in world.world:
                            continue
                        p[i] -= (d - pad) * face[i]
                        if face == (0, -1, 0) or face == (0, 1, 0):
                            # You are colliding with the ground or ceiling, so stop
                            # falling / rising.
                            self.dy = 0
                        break
            return tuple(p)
        
    def get_motion_vector(character):

            """ Returns the current motion vector indicating the velocity of the
            player.

            Returns
            -------
            vector : tuple of len 3
            Tuple containing the velocity in x, y, and z respectively.

            """
            if any(character.strafe):
                x, y = character.rotation
                strafe = math.degrees(math.atan2(*character.strafe))
                y_angle = math.radians(y)
                x_angle = math.radians(x + strafe)
                if character.flying:
                    m = math.cos(y_angle)
                    dy = math.sin(y_angle)
                    if character.strafe[1]:
                        # Moving left or right.
                        dy = 0.0
                        m = 1
                    if character.strafe[0] > 0:
                        # Moving backwards.
                        dy *= -1
                    # When you are flying up or down, you have less left and right
                    # motion.
                    dx = math.cos(x_angle) * m
                    dz = math.sin(x_angle) * m
                else:
                    dy = 0.0
                    dx = math.cos(x_angle)
                    dz = math.sin(x_angle)
            else:
                dy = 0.0
                dx = 0.0
                dz = 0.0
            return (dx, dy, dz)
    
    def get_sight_vector(self):
        """ Returns the current line of sight vector indicating the direction
        the player is looking.

        """
        x, y = self.rotation
        # y ranges from -90 to 90, or -pi/2 to pi/2, so m ranges from 0 to 1 and
        # is 1 when looking ahead parallel to the ground and 0 when looking
        # straight up or down.
        m = math.cos(math.radians(y))
        # dy ranges from -1 to 1 and is -1 when looking straight down and 1 when
        # looking straight up.
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)

    def rotation(self):
        return self.rotation
    
    def playerMove(self, dt, world):
        """ Private implementation of the `update()` method. This is where most
        of the motion logic lives, along with gravity and collision detection.

        Parameters
        ----------
        dt : float
            The change in time since the last call.

        """
        #Check and change dy for jumping
        if (self.jumping == True and self.jumped == False):
            self.dy = JUMP_SPEED
        
        # walking
        speed = FLYING_SPEED if self.flying else WALKING_SPEED
        d = dt * speed # distance covered this tick.
        dx, ody, dz = self.get_motion_vector()
        # New position in space, before accounting for gravity.
        dx, dy, dz = dx * d, ody * d, dz * d
        # gravity
        if not self.flying:
            # Update your vertical speed: if you are falling, speed up until you
            # hit terminal velocity; if you are jumping, slow down until you
            # start falling.
            self.dy -= dt * GRAVITY
            self.dy = max(self.dy, -TERMINAL_VELOCITY)
            dy += self.dy * dt
        # collisions
        x, y, z = self.position
        x, y, z = self.collide((x + dx, y + dy, z + dz), PLAYER_HEIGHT, world)
        self.position = (x, y, z)
        if self.dy == 0:
            self.jumped = False
        else:
            self.jumped = True
    
    def hitBlock(self):
        pass