import pychrono as chrono

print("PyChrono import OK")

sys = chrono.ChSystemNSC()
sys.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)
sys.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, -9.81))
dt = 1e-4

mat = chrono.ChContactMaterialNSC()
mat.SetFriction(0.6)

floor = chrono.ChBodyEasyBox(1.0, 1.0, 0.1, 1000, True, True, mat)
floor.SetFixed(True)
floor.SetPos(chrono.ChVector3d(0, 0, -0.05))
sys.Add(floor)

ball = chrono.ChBodyEasySphere(0.1, 2700, True, True, mat)
ball.SetPos(chrono.ChVector3d(0, 0, 1.0))
sys.Add(ball)

for step in range(8000):
    sys.DoStepDynamics(dt)
    if step % 1600 == 0:
        z = ball.GetPos().z
        print(f"t={step*dt:.3f}s  ball.z={z:.4f}")