C     LOANPAY.f - Loan payment calculation system
C     Legacy FORTRAN 77 code from banking system (1970s)
C     Calculates amortization schedules for mortgages and loans

      PROGRAM LOANPAY
      IMPLICIT NONE

C     Variable declarations
      REAL PRINCIPAL, RATE, PAYMENT, BALANCE, INTEREST
      REAL TOTINT, TOTPRIN
      INTEGER NYEARS, NMONTHS, MONTH
      CHARACTER*20 LOANTYPE

C     Print header
      WRITE(*,*) '========================================='
      WRITE(*,*) '   LOAN AMORTIZATION CALCULATOR'
      WRITE(*,*) '   FIRST NATIONAL BANK SYSTEM v2.3'
      WRITE(*,*) '========================================='
      WRITE(*,*)

C     Input loan parameters
      WRITE(*,*) 'Enter loan amount ($):'
      READ(*,*) PRINCIPAL
      WRITE(*,*) 'Enter annual interest rate (%):'
      READ(*,*) RATE
      WRITE(*,*) 'Enter loan term (years):'
      READ(*,*) NYEARS
      WRITE(*,*) 'Enter loan type (FIXED/VARIABLE):'
      READ(*,'(A)') LOANTYPE

C     Validate inputs
      IF (PRINCIPAL .LE. 0.0) THEN
         WRITE(*,*) 'ERROR: Principal must be positive'
         STOP
      END IF

      IF (RATE .LE. 0.0 .OR. RATE .GT. 50.0) THEN
         WRITE(*,*) 'ERROR: Invalid interest rate'
         STOP
      END IF

C     Calculate monthly payment
      NMONTHS = NYEARS * 12
      RATE = RATE / 100.0 / 12.0  ! Convert to monthly rate

      IF (RATE .GT. 0.0) THEN
         PAYMENT = PRINCIPAL * (RATE * (1+RATE)**NMONTHS) /
     &             ((1+RATE)**NMONTHS - 1)
      ELSE
         PAYMENT = PRINCIPAL / NMONTHS
      END IF

C     Print loan summary
      WRITE(*,*)
      WRITE(*,*) 'LOAN SUMMARY:'
      WRITE(*,*) '------------'
      WRITE(*,100) 'Principal:       $', PRINCIPAL
      WRITE(*,101) 'Annual Rate:      ', RATE*12.0*100.0, '%'
      WRITE(*,102) 'Term:            ', NYEARS, ' years'
      WRITE(*,100) 'Monthly Payment: $', PAYMENT
      WRITE(*,*)

C     Generate amortization schedule
      WRITE(*,*) 'AMORTIZATION SCHEDULE:'
      WRITE(*,*) 'Month  Payment    Interest  Principal  Balance'
      WRITE(*,*) '-----  ---------  --------  ---------  ---------'

      BALANCE = PRINCIPAL
      TOTINT = 0.0
      TOTPRIN = 0.0

      DO 200 MONTH = 1, NMONTHS
         INTEREST = BALANCE * RATE

C        Adjust last payment for rounding
         IF (MONTH .EQ. NMONTHS) THEN
            PAYMENT = BALANCE + INTEREST
         END IF

         TOTINT = TOTINT + INTEREST
         TOTPRIN = TOTPRIN + (PAYMENT - INTEREST)
         BALANCE = BALANCE - (PAYMENT - INTEREST)

C        Print every 12th month or last month
         IF (MOD(MONTH, 12) .EQ. 0 .OR. MONTH .EQ. NMONTHS) THEN
            WRITE(*,103) MONTH, PAYMENT, INTEREST,
     &                   (PAYMENT - INTEREST), BALANCE
         END IF

 200  CONTINUE

C     Print totals
      WRITE(*,*) '-----  ---------  --------  ---------  ---------'
      WRITE(*,100) 'Total Interest: $', TOTINT
      WRITE(*,100) 'Total Paid:     $', TOTINT + PRINCIPAL

C     Format statements
 100  FORMAT(A,F12.2)
 101  FORMAT(A,F6.3,A)
 102  FORMAT(A,I3,A)
 103  FORMAT(I5,2X,F9.2,2X,F8.2,2X,F9.2,2X,F9.2)

      WRITE(*,*)
      WRITE(*,*) 'End of calculation'

      STOP
      END
