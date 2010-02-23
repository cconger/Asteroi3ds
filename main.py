##############################################################################
##
##  ASTEROI3DS
##
##  Channing Conger
##    For GAME2150 at Northeastern University
##
##  For Use with Panda3d Version 1.7
##
##  2-16-2010
##
##############################################################################

#TODO: Radar UI Element

from math   import pi,sin,cos
from random import randint, choice, random
import sys

from direct.showbase.ShowBase       import ShowBase
from direct.showbase.DirectObject   import DirectObject
from direct.task.Task               import Task
from direct.gui.OnscreenText        import OnscreenText
from direct.interval.IntervalGlobal import *
from panda3d.core                   import TextNode
from panda3d.core                   import WindowProperties
from panda3d.core                   import Point3, Vec3, VBase4, Vec4
from panda3d.core                   import CompassEffect
from panda3d.core                   import NodePath
from panda3d.core                   import CollisionTraverser, CollisionHandlerEvent
from panda3d.core                   import CollisionNode, CollisionSphere
from panda3d.core                   import DirectionalLight, PointLight

game = ShowBase()

DEBUG_CONTROLS        = False
DEBUG_DISPLAY_TEXT    = False

##  Game Settings=============================================================
INVERTED_MOUSE        = 1    # Set to -1 for no inverted mouse
ROTATION_RATE         = 0.1  # Sensitivity to mouse movement
MOUSE_OFFSET          = 200  # Approximating the center of the screen
ASTEROID_DEFAULT_SIZE = 3    # Default Asteroid Size
ASTEROID_MULTIPLY     = 3    # Number of Asteroids spawned on hit
ASTEROID_SPEED        = 2    # Speed that Asteroids move at
ASTEROID_START_COUNT  = 10   # Number of Asteroids to Spawn
ASTEROID_SPIN_SPEED   = 20   # How fast Asteroids Spin
ASTEROID_SPAWN_MAX    = 100  # Max distance Asteroids Spawn from ship
ASTEROID_SPAWN_MIN    = 20   # Min distance Asteroids Spawn from ship
SHIP_MAX_SPEED        = 10   # Maximum ship speed
SHIP_ACCEL_RATE       = 5    # How fast ship accelerates
SHIP_SIZE             = 1.5  # How large the Ship is.
BULLET_FIRE_SPEED     = 25   # How fast bullets go above ship speed
BULLET_TRAVEL_TIME    = 10   # How long bullets live after fired
BULLET_SIZE           = 0.05 # Visually how large the bullets are
GAME_OVER_DELAY       = 5    # How many seconds to display the score at the end

###
# Ship
#
#  Represents the Spacecraft that the player is controlling.
##
class Ship(DirectObject):
  def __init__(self, collisionHandler):
    self.collHandler = collisionHandler
    # Load Model--------------------------------------------------------------
    self.model = loader.loadModel('Models/bullet.egg.pz')
    self.model.setPythonTag("owner", self)
    self.model.reparentTo(render)

    # Load Light-------------------------------------------------------------
    self.lamp = DirectionalLight('shipdlight')
    self.lamp.setColor(VBase4(0.8,0.8,0.5,1))
    self.lampNodePath = self.model.attachNewNode(self.lamp)
    self.lampNodePath.setHpr(0,15,0)
    render.setLight(self.lampNodePath)

    # Add Movment Update Task------------------------------------------------
    self.movementTask = taskMgr.add(self.updatePosition, "ship-movement-task")
    self.movementTask.last = 0
    self.bullets = []
    self.reset()

    self.collisionNode = self.model.attachNewNode(CollisionNode("ship"))
    self.collisionNode.node().addSolid(CollisionSphere(0,0,0,1))
    base.cTrav.addCollider(self.collisionNode, self.collHandler)

    self.accept('asteroid-into-ship', self.collideWithAsteroid)

  #--Accessors----------------------------------------------------------------
  def getModel(self):
    return self.model

  def getFacingHpr(self):
    return self.getModel().getHpr()

  def getFacingVec(self):
    return self.getModel().getQuat().getForward()

  def getVelVec(self):
    return self.velocity

  def getVel(self):
    return self.velocity.length()

  def getPos(self):
    return self.model.getPos()

  def isAlive(self):
    return self.alive

  ###
  # Ship.fireBullet
  #
  # Spawns and launches bullet in teh direction that the player is currently
  #  facing.
  ##
  def fireBullet(self):
    bulletPosition = self.getPos() + (self.getFacingVec() * (SHIP_SIZE + .05))
    bulletVelocity = self.getVelVec() + (self.getFacingVec() * BULLET_FIRE_SPEED)
    bullet = Bullet(self,
                    bulletPosition,
                    bulletVelocity,
                    self.collHandler)
    self.bullets.append(bullet)
    taskMgr.doMethodLater(BULLET_TRAVEL_TIME,
                          self.removeBullet,
                          "expire_bullet"+str(self.bullets.index(bullet)),
                          [bullet])

  ###
  # Ship.removeBullet(bullet)
  #
  #   Removes given bullet from list of updated bullets, and destroys instance
  ##
  def removeBullet(self, bullet):
    if(self.bullets.count(bullet) > 0):
      self.bullets.remove(bullet)
      bullet.remove()
    return Task.done

  ###
  # Ship.updatePosition
  #
  # Body for the task.  Calculates delta in time since last frame, and updates
  #   position based on the current velocity
  ##
  def updatePosition(self, task):
    dt = task.time - task.last
    task.last = task.time

    self.model.setPos(self.getPos() + (self.getVelVec() * dt))
    return Task.cont

  ###
  # Ship.rotate
  #
  # Encapsulated helper for the for rotation hprDelta is the relative rotation
  ##
  def rotate(self, hprDelta):
    self.model.setHpr(self.model, hprDelta)

  ###
  # Ship.accelerate
  #
  # Encapsulated helper for accelerating the ship.  Determines current facing
  # unit vector and multiplies by accleration rate * impulse duration
  ##
  def accelerate(self, timeAccelerating):
    self.velocity += self.getFacingVec() * SHIP_ACCEL_RATE * timeAccelerating
    if self.velocity.length() > SHIP_MAX_SPEED:
      self.velocity = (self.velocity / self.velocity.length()) * SHIP_MAX_SPEED

  ###
  # Ship.stop
  #
  # Method for resetting the speed of the ship (for debug purposes)
  ##
  def stop(self):
    self.velocity = Vec3(0,0,0)

  ###
  # Ship.collideWithAsteroid
  #
  # Event handler for collision of Asteroid Into Ship
  ##
  def collideWithAsteroid(self, entry):
    self.alive = False
    messenger.send('resetgame')

  ###
  # Ship.reset
  #
  # Helper method for resetting all aspects of the ship class
  ##
  def reset(self):
    self.model.setPos(Vec3(0,0,0))
    self.model.setHpr(Vec3(0,0,0))
    self.velocity = Vec3(0,0,0)
    self.alive = True
    for bullet in self.bullets:
      self.bullets.remove(bullet)
      bullet.remove()

##############################################################################
##  World Class
##
##  Contains and Keeps track of all other elements
##############################################################################
class World(DirectObject):
  def __init__(self):
    #--Collision Handler------------------------------------------------------
    self.collHandler = CollisionHandlerEvent()
    self.collHandler.addInPattern('%fn-into-%in')
    base.cTrav = CollisionTraverser('world traverser')

    #--Mouse Control----------------------------------------------------------
    base.disableMouse()
    self.properties = WindowProperties()
    self.properties.setCursorHidden(True)
    base.win.requestProperties(self.properties)

    #--Register Hud Elements--------------------------------------------------
    self.instruction1 = self.addInstruction("[click] to Shoot",2)
    self.instruction2 = self.addInstruction("[a] to accelerate", 1)
    self.instruction3 = self.addInstruction("[esc] to quit", 0)

    self.scoreHud = self.addHudElement("", 0)
    self.accuracy = self.addHudElement("", 1)
    self.speedHud = self.addHudElement("", 2)

    self.bigHud = OnscreenText(text="", style=1, fg=(1,1,1,1), pos=(0,0), align=TextNode.ACenter, scale = .1)

    #--Load Objects and Models------------------------------------------------
    self.ship = Ship(self.collHandler)
    self.loadSkyBox()
    game.camera.reparentTo(self.ship.getModel())

    #--Start Game-------------------------------------------------------------
    self.asteroids = []
    self.resetGame()

    #--Controls --------------------------------------------------------------
    self.keysDown = {'a': 0}

    self.controlTask = taskMgr.add(self.gameLoop, "game-control-task")
    self.controlTask.lastTime = 0

    self.accept("escape", sys.exit, [0])
    self.accept("a", self.keyDown, ['a'])
    self.accept("a-up", self.keyUp, ['a'])
    self.accept("mouse1", self.shoot)
    self.accept("space", self.shoot)
    self.accept("resetgame", self.gameOver)

    if(DEBUG_CONTROLS):
      self.accept("0", self.ship.stop)
      self.accept("9", self.ship.getModel().setHpr, [0,0,0])

    #--Register CollisionEvent Handlers---------------------------------------
    self.accept('asteroid-into-bullet', self.bulletAsteroidCollision)

  ###
  # World.shoot:
  #
  # Dispatch method that overloads the use of the mouse button
  ##
  def shoot(self):
    if(self.ship.isAlive()):
      self.ship.fireBullet()
      self.shots += 1
    else:
      self.resetGame()

  ###
  # World.gameOver()
  #
  #  Displays "Game Over: <SCORE>" then resets game after 5 seconds
  def gameOver(self):
    self.bigHud.setText("GAME OVER: " + str(self.score))
    taskMgr.doMethodLater(GAME_OVER_DELAY,
                          self.resetGame,
                          "reset_game",
                          [])


  ###
  # World.resetGame
  #
  # Resets anything that might change during play essentially reloading
  ##
  def resetGame(self):
    for asteroid in self.asteroids:
      asteroid.remove()
    self.score       = 0
    self.shots       = 0
    self.hits        = 0
    self.lifeLength  = 0
    self.ship.reset()
    self.scoreHud.setText("Score     : " + str(self.score))
    self.accuracy.setText("Hit/Fired : 0/0")
    self.speedHud.setText("Speed     : 0")
    self.bigHud.setText("")
    self.loadAsteroids()

  ###
  # World.bulletAsteroidCollision:
  #
  # Event Handler for collision From Asteroid Into Bullet
  # Triggers the "explosion" of an Asteroid and appends replacments
  ##
  def bulletAsteroidCollision(self, entry):
    bullet = entry.getIntoNodePath().getParent().getPythonTag("owner")
    asteroid = entry.getFromNodePath().getParent().getPythonTag("owner")
    self.ship.removeBullet(bullet)
    self.asteroids.extend(asteroid.registerHit())
    self.asteroids.remove(asteroid)
    self.score += 100
    self.hits += 1
    asteroid.remove()

  ###
  # World.keyDown:
  #
  # Register the given key as being held down
  ##
  def keyDown(self, key):
    self.keysDown[key] = 1

  ###
  # World.keyUp:
  #
  # Register the given key as no longer being held down
  ##
  def keyUp(self, key):
    self.keysDown[key] = 0

  ###
  # World.addHudElement(msg, row)
  #
  # Displays the given string msg in the top left with a row offset of row
  ##
  def addHudElement(self, msg, row):
    return OnscreenText(text=msg, style=1, fg=(1,1,1,1),
        pos=(-1.3,.95 - (.05 * row)), align=TextNode.ALeft, scale = .05)

  ###
  # World.addInstruction(msg, row)
  #
  # Displays the given string msg in the top right with a row offset of row
  ##
  def addInstruction(self, msg, row):
    return OnscreenText(text=msg, style=1, fg=(1,1,1,1),
        pos=(1.3,.95 - (.05 * row)), align=TextNode.ARight, scale = .05)

  ###
  # World.loadSkyBox:
  #
  # Helper method that loads the skybox, sets size and other factors and
  # parents to ship, while keeping a compass effect so it will spin around the 
  # ship
  ##
  def loadSkyBox(self):
    self.skybox = game.loader.loadModel("Models/skybox.egg")
    self.skybox.setScale(100.0,100.0,100.0)
    self.skybox.setPos(0,0,0)
    self.skybox.reparentTo(self.ship.getModel())
    # Roots the skybox with relation to the render node, making it stationary
    # even though its parented to the ship
    self.skybox.setEffect(CompassEffect.make(render, CompassEffect.PRot))

  ###
  # gameLoop
  #
  # Task for managing the input from the mouse and keys. In addition updating
  # the game world.
  ##
  def gameLoop(self, task):
    md = base.win.getPointer(0)
    x = md.getX()
    y = md.getY()

    # Get the delta in time since last frame (allows us to ratelimit rotation
    #   and acceleration
    dt = task.time - task.lastTime
    task.lastTime = task.time
    self.lifeLength += dt

    # Calculate how far the mouse moved, generate a rotation offest and send
    #  to the ship to rotate
    if base.win.movePointer(0, MOUSE_OFFSET, MOUSE_OFFSET):
      self.ship.rotate(Vec3(-((x-MOUSE_OFFSET) * ROTATION_RATE),
                            INVERTED_MOUSE*((y-MOUSE_OFFSET) * ROTATION_RATE),
                            0))

    #--Allows Holding of A key------------------------------------------------

    if(self.keysDown['a'] == 1):
      self.ship.accelerate(dt)
    
    #--Update Asteroid Positions----------------------------------------------
    for asteroid in self.asteroids:
      asteroid.updatePos(dt)

    #--Update HUD-------------------------------------------------------------
    if(self.shots !=0):
      self.accuracy.setText("Hit/Fired : " + str(self.hits) + "/" + str(self.shots))

    self.scoreHud.setText("Score     : " + str(self.score))
    self.speedHud.setText("Speed     : " + str(self.ship.getVel()))

    return Task.cont

  ###
  # World.loadAsteroids
  #
  # Helper method for creating the asteroids
  ##
  def loadAsteroids(self):
    self.asteroids = []
    for i in range(ASTEROID_START_COUNT):
      x = choice([-1,1]) * choice(range(ASTEROID_SPAWN_MIN, ASTEROID_SPAWN_MAX))
      y = choice([-1,1]) * choice(range(ASTEROID_SPAWN_MIN, ASTEROID_SPAWN_MAX))
      z = choice([-1,1]) * choice(range(ASTEROID_SPAWN_MIN, ASTEROID_SPAWN_MAX))
      self.asteroids.append(Asteroid(Vec3(x,y,z), self.collHandler))

###
# Bullet
#
# Object for tracking a bullet object.
##
class Bullet(DirectObject):
  def __init__(self, ship, bulletPos, bulletVelocityVec, collisionHandler):
    self.model = game.loader.loadModel("Models/bullet.egg.pz")
    self.model.setPos(bulletPos)
    self.model.setScale(BULLET_SIZE)
    self.model.reparentTo(render)
    self.model.setPythonTag("owner", self)
    self.ship = ship
    finalPosition = bulletPos + (bulletVelocityVec * BULLET_TRAVEL_TIME)
    self.trajectory = self.model.posInterval(BULLET_TRAVEL_TIME, finalPosition).start()

    self.collisionNode = self.model.attachNewNode(CollisionNode("bullet"))
    self.collisionNode.node().addSolid(CollisionSphere(0,0,0,1))
    base.cTrav.addCollider(self.collisionNode, collisionHandler)

    # Add Point Light to the bullet
    self.plight = PointLight('plight'+str(random()))
    self.plight.setColor(Vec4(1,1,1,1))
    self.plight.setAttenuation(Vec3(0.7, 0.05, 0))
    self.plnp = self.model.attachNewNode(self.plight)
    render.setLight(self.plnp)
    render.setShaderInput("light", self.plnp)


  ###
  # Bullet.remove
  #
  #  Removes this asteroid from rendering and registering collisions.
  ## 
  def remove(self):
    self.ignoreAll()
    self.model.remove()
    self.collisionNode.remove()

###
# Asteroid
#
#  Object for tracking Asteroids
##
class Asteroid(DirectObject):
  def __init__(self, positionVector, collisionHandler, size=ASTEROID_DEFAULT_SIZE):
    self.model = game.loader.loadModel("Models/asteroid.egg.pz")
    self.model.setTexture(loader.loadTexture("Models/asteroid_tex"+str(choice([0,1,2]))+".jpg"))
    self.model.setPos(positionVector)
    self.size = size
    self.model.setScale(self.size)
    self.model.setHpr(0,0,0)
    self.model.reparentTo(render)
    self.model.setPythonTag("owner", self)
    self.velocity = Vec3((random() * 2) - 1,
                         (random() * 2) - 1,
                         (random() * 2) - 1) * ASTEROID_SPEED
    self.collisionHandler = collisionHandler
    
    self.collisionNode = self.model.attachNewNode(CollisionNode("asteroid"))
    self.collisionNode.node().addSolid(CollisionSphere(0,0,0,1))
    base.cTrav.addCollider(self.collisionNode, collisionHandler)

    spinHprInterval1 = self.model.hprInterval(ASTEROID_SPIN_SPEED / 2,
                           Point3(180,0,0),
                           startHpr=Point3(0,0,0))
    spinHprInterval2 = self.model.hprInterval(ASTEROID_SPIN_SPEED / 2,
                           Point3(360,0,0),
                           startHpr=Point3(180,0,0))
    self.spin = Sequence(spinHprInterval1, spinHprInterval2, name="spinAsteroid"+str(random()))
    self.spin.loop()

  def updatePos(self, timeElapsed):
    self.model.setPos(self.model.getPos() + (self.velocity) * timeElapsed)

  ###
  # Asteroid.remove
  #
  #  Removes this asteroid from rendering and registering collisions.
  ## 
  def remove(self):
    self.ignoreAll()
    self.model.remove()
    self.collisionNode.remove()
    #Remove collider?

  ###
  # Asteroid.registerHit
  #
  #  Event Handler called from the world.  This generates a list of
  #    replacements asteroids for this asteroid after it gets hit.
  #  If the size is 1 then it just destroys this Asteroid and returns
  #    an empty replacment list
  ##
  def registerHit(self):
    newAsteroids = []
    if(self.size > 1):
      for i in range(ASTEROID_MULTIPLY):
        randomVec = Vec3(random() * (-1^i),
                         random() * (-1^(i-1)),
                         random() * (-1^i)) * self.size / 2
        asteroid = Asteroid(self.model.getPos() + randomVec,
                            self.collisionHandler,
                            self.size - 1)
        newAsteroids.append(asteroid)
    return newAsteroids

world = World()

game.run()
