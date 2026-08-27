"
Counter - A simple counter class
Demonstrates basic Smalltalk class definition and methods
"

Object subclass: #Counter
    instanceVariableNames: 'count'
    classVariableNames: ''
    poolDictionaries: ''
    category: 'Examples'

!Counter methodsFor: 'initialization'!

initialize
    "Initialize the counter to zero"
    super initialize.
    count := 0
! !

!Counter methodsFor: 'accessing'!

count
    "Return the current count"
    ^ count
!

count: aNumber
    "Set the count to a specific number"
    count := aNumber
! !

!Counter methodsFor: 'operations'!

increment
    "Increment the counter by one"
    count := count + 1.
    ^ count
!

decrement
    "Decrement the counter by one"
    count := count - 1.
    ^ count
!

incrementBy: amount
    "Increment the counter by the specified amount"
    count := count + amount.
    ^ count
!

reset
    "Reset the counter to zero"
    count := 0
! !

!Counter methodsFor: 'testing'!

isZero
    "Test if the counter is zero"
    ^ count = 0
!

isPositive
    "Test if the counter is positive"
    ^ count > 0
!

isNegative
    "Test if the counter is negative"
    ^ count < 0
! !

!Counter methodsFor: 'printing'!

printOn: aStream
    "Print a textual representation"
    super printOn: aStream.
    aStream nextPutAll: ' (count: '.
    count printOn: aStream.
    aStream nextPutAll: ')'
! !

!Counter class methodsFor: 'instance creation'!

new
    "Create a new counter instance"
    ^ super new initialize
!

startingAt: aNumber
    "Create a new counter with an initial value"
    ^ self new count: aNumber
! !
