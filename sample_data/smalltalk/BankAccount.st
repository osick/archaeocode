"
BankAccount - Cincom VisualWorks style Smalltalk
Demonstrates namespace syntax and typical Cincom patterns
"

Smalltalk.Examples defineClass: #BankAccount
    superclass: #{Core.Object}
    indexedType: #none
    private: false
    instanceVariableNames: 'accountNumber balance owner transactionHistory'
    classInstanceVariableNames: ''
    imports: ''
    category: 'Examples-Banking'

!BankAccount methodsFor: 'initialization'!

initialize
    "Initialize a new bank account"
    super initialize.
    balance := 0.
    transactionHistory := OrderedCollection new.
    accountNumber := self class generateAccountNumber
! !

!BankAccount methodsFor: 'accessing'!

accountNumber
    "Return the account number"
    ^ accountNumber
!

balance
    "Return the current balance"
    ^ balance
!

owner
    "Return the account owner"
    ^ owner
!

owner: aCustomer
    "Set the account owner"
    owner := aCustomer
!

transactionHistory
    "Return the transaction history"
    ^ transactionHistory
! !

!BankAccount methodsFor: 'operations'!

deposit: amount
    "Deposit money into the account"
    | transaction |
    amount <= 0 ifTrue: [
        ^ self error: 'Deposit amount must be positive'
    ].
    balance := balance + amount.
    transaction := Dictionary new
        at: #type put: #deposit;
        at: #amount put: amount;
        at: #timestamp put: Timestamp now;
        at: #balanceAfter put: balance;
        yourself.
    transactionHistory add: transaction.
    ^ balance
!

withdraw: amount
    "Withdraw money from the account"
    | transaction |
    amount <= 0 ifTrue: [
        ^ self error: 'Withdrawal amount must be positive'
    ].
    balance < amount ifTrue: [
        ^ self error: 'Insufficient funds'
    ].
    balance := balance - amount.
    transaction := Dictionary new
        at: #type put: #withdrawal;
        at: #amount put: amount;
        at: #timestamp put: Timestamp now;
        at: #balanceAfter put: balance;
        yourself.
    transactionHistory add: transaction.
    ^ balance
!

transferTo: anotherAccount amount: amount
    "Transfer money to another account"
    self withdraw: amount.
    anotherAccount deposit: amount.
    ^ balance
! !

!BankAccount methodsFor: 'testing'!

canWithdraw: amount
    "Test if withdrawal is possible"
    ^ balance >= amount and: [ amount > 0 ]
!

hasPositiveBalance
    "Test if balance is positive"
    ^ balance > 0
!

isOverdrawn
    "Test if account is overdrawn"
    ^ balance < 0
! !

!BankAccount methodsFor: 'reporting'!

printStatementOn: aStream
    "Print account statement"
    aStream
        nextPutAll: 'Account: ';
        nextPutAll: accountNumber printString;
        cr;
        nextPutAll: 'Owner: ';
        nextPutAll: owner printString;
        cr;
        nextPutAll: 'Balance: $';
        nextPutAll: balance printString;
        cr;
        nextPutAll: 'Transactions: ';
        nextPutAll: transactionHistory size printString;
        cr.
    self printTransactionsOn: aStream
!

printTransactionsOn: aStream
    "Print transaction history"
    transactionHistory do: [ :txn |
        aStream
            nextPutAll: (txn at: #timestamp) printString;
            nextPutAll: ' - ';
            nextPutAll: (txn at: #type) printString;
            nextPutAll: ': $';
            nextPutAll: (txn at: #amount) printString;
            nextPutAll: ' (Balance: $';
            nextPutAll: (txn at: #balanceAfter) printString;
            nextPutAll: ')';
            cr
    ]
! !

!BankAccount class methodsFor: 'instance creation'!

new
    "Create a new bank account"
    ^ super new initialize
!

forOwner: aCustomer
    "Create a new account for a customer"
    ^ self new
        owner: aCustomer;
        yourself
!

forOwner: aCustomer withInitialDeposit: amount
    "Create a new account with initial deposit"
    ^ (self forOwner: aCustomer)
        deposit: amount;
        yourself
! !

!BankAccount class methodsFor: 'private'!

generateAccountNumber
    "Generate a unique account number"
    ^ 'ACC', (Timestamp now asSeconds printString),
      (Random new nextInt: 9999) printString
! !
