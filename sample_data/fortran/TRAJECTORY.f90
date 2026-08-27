! TRAJECTORY.f90 - Projectile trajectory calculation system
! Legacy scientific computing code from 1980s aerospace system
! Calculates missile trajectory with atmospheric drag

      PROGRAM TRAJECTORY
      IMPLICIT NONE

      ! Variable declarations
      REAL*8 :: velocity, angle, gravity, drag_coef
      REAL*8 :: time_step, max_time, current_time
      REAL*8 :: x_pos, y_pos, x_vel, y_vel
      REAL*8 :: air_density, cross_section, mass
      REAL*8 :: drag_force, drag_x, drag_y
      INTEGER :: num_steps, i
      LOGICAL :: hit_ground

      ! Initialize constants
      gravity = 9.81D0
      air_density = 1.225D0
      cross_section = 0.05D0
      mass = 10.0D0
      drag_coef = 0.47D0

      ! Input parameters
      WRITE(*,*) 'PROJECTILE TRAJECTORY CALCULATOR'
      WRITE(*,*) '================================='
      WRITE(*,*) 'Enter initial velocity (m/s):'
      READ(*,*) velocity
      WRITE(*,*) 'Enter launch angle (degrees):'
      READ(*,*) angle

      ! Convert angle to radians
      angle = angle * 3.14159265D0 / 180.0D0

      ! Initialize position and velocity
      x_pos = 0.0D0
      y_pos = 0.0D0
      x_vel = velocity * COS(angle)
      y_vel = velocity * SIN(angle)

      ! Simulation parameters
      time_step = 0.01D0
      max_time = 100.0D0
      current_time = 0.0D0
      hit_ground = .FALSE.

      ! Open output file
      OPEN(UNIT=10, FILE='trajectory.dat', STATUS='REPLACE')
      WRITE(10,*) 'Time(s),X(m),Y(m),Vx(m/s),Vy(m/s)'

      ! Main simulation loop
      DO WHILE (current_time < max_time .AND. .NOT. hit_ground)
         ! Calculate drag force
         drag_force = 0.5D0 * air_density * drag_coef * cross_section
         drag_force = drag_force * (x_vel**2 + y_vel**2)

         ! Decompose drag into components
         drag_x = -drag_force * x_vel / SQRT(x_vel**2 + y_vel**2)
         drag_y = -drag_force * y_vel / SQRT(x_vel**2 + y_vel**2)

         ! Update velocities (F=ma)
         x_vel = x_vel + (drag_x / mass) * time_step
         y_vel = y_vel + ((drag_y / mass) - gravity) * time_step

         ! Update positions
         x_pos = x_pos + x_vel * time_step
         y_pos = y_pos + y_vel * time_step

         ! Write output
         WRITE(10,100) current_time, x_pos, y_pos, x_vel, y_vel

         ! Check if projectile hit ground
         IF (y_pos < 0.0D0) THEN
            hit_ground = .TRUE.
            WRITE(*,*) 'IMPACT!'
            WRITE(*,101) 'Range: ', x_pos, ' meters'
            WRITE(*,102) 'Flight time: ', current_time, ' seconds'
         END IF

         current_time = current_time + time_step
      END DO

      ! Close output file
      CLOSE(10)

      ! Format statements
 100  FORMAT(F8.3,',',F10.2,',',F10.2,',',F8.2,',',F8.2)
 101  FORMAT(A,F10.2,A)
 102  FORMAT(A,F8.3,A)

      WRITE(*,*) 'Trajectory data saved to trajectory.dat'

      END PROGRAM TRAJECTORY


      ! Subroutine for atmospheric density calculation
      SUBROUTINE ATMOSPHERE(altitude, density)
      IMPLICIT NONE
      REAL*8, INTENT(IN) :: altitude
      REAL*8, INTENT(OUT) :: density
      REAL*8 :: scale_height

      scale_height = 8500.0D0  ! meters
      density = 1.225D0 * EXP(-altitude / scale_height)

      RETURN
      END SUBROUTINE ATMOSPHERE
