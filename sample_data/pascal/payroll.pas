{ PAYROLL.PAS - Employee Payroll Calculation System }
{ Legacy Pascal code from 1980s HR/Payroll system }
{ Calculates wages, taxes, and deductions }

program PayrollSystem;

uses
  Crt;

const
  MaxEmployees = 500;
  FederalTaxRate = 0.15;
  StateTaxRate = 0.05;
  SocialSecurityRate = 0.062;
  MedicareRate = 0.0145;

type
  EmployeeType = (Hourly, Salaried, Contract);

  EmployeeRecord = record
    EmployeeID: Integer;
    FirstName: string[30];
    LastName: string[30];
    Department: string[20];
    EmpType: EmployeeType;
    HourlyRate: Real;
    AnnualSalary: Real;
    HoursWorked: Real;
    OvertimeHours: Real;
    Active: Boolean;
  end;

  PaycheckRecord = record
    EmployeeID: Integer;
    GrossPay: Real;
    FederalTax: Real;
    StateTax: Real;
    SocialSecurity: Real;
    Medicare: Real;
    TotalDeductions: Real;
    NetPay: Real;
  end;

var
  Employees: array[1..MaxEmployees] of EmployeeRecord;
  EmployeeCount: Integer;

{ Function to calculate gross pay }
function CalculateGrossPay(const Emp: EmployeeRecord): Real;
var
  RegularPay, OvertimePay: Real;
begin
  case Emp.EmpType of
    Hourly:
      begin
        RegularPay := Emp.HoursWorked * Emp.HourlyRate;
        OvertimePay := Emp.OvertimeHours * Emp.HourlyRate * 1.5;
        CalculateGrossPay := RegularPay + OvertimePay;
      end;
    Salaried:
      begin
        { Bi-weekly salary }
        CalculateGrossPay := Emp.AnnualSalary / 26.0;
      end;
    Contract:
      begin
        { Contract pay based on hours }
        CalculateGrossPay := Emp.HoursWorked * Emp.HourlyRate;
      end;
  end;
end;

{ Procedure to calculate taxes and deductions }
procedure CalculateDeductions(GrossPay: Real; var Paycheck: PaycheckRecord);
begin
  Paycheck.FederalTax := GrossPay * FederalTaxRate;
  Paycheck.StateTax := GrossPay * StateTaxRate;
  Paycheck.SocialSecurity := GrossPay * SocialSecurityRate;
  Paycheck.Medicare := GrossPay * MedicareRate;

  Paycheck.TotalDeductions := Paycheck.FederalTax +
                               Paycheck.StateTax +
                               Paycheck.SocialSecurity +
                               Paycheck.Medicare;

  Paycheck.NetPay := GrossPay - Paycheck.TotalDeductions;
end;

{ Procedure to generate paycheck for employee }
procedure GeneratePaycheck(const Emp: EmployeeRecord);
var
  Paycheck: PaycheckRecord;
begin
  Paycheck.EmployeeID := Emp.EmployeeID;
  Paycheck.GrossPay := CalculateGrossPay(Emp);

  CalculateDeductions(Paycheck.GrossPay, Paycheck);

  { Display paycheck }
  ClrScr;
  WriteLn('=========================================');
  WriteLn('       EMPLOYEE PAYCHECK STUB');
  WriteLn('=========================================');
  WriteLn;
  WriteLn('Employee: ', Emp.FirstName, ' ', Emp.LastName);
  WriteLn('ID: ', Emp.EmployeeID);
  WriteLn('Department: ', Emp.Department);
  WriteLn;

  case Emp.EmpType of
    Hourly:
      begin
        WriteLn('Type: Hourly');
        WriteLn('Hourly Rate: $', Emp.HourlyRate:0:2);
        WriteLn('Regular Hours: ', Emp.HoursWorked:0:2);
        WriteLn('Overtime Hours: ', Emp.OvertimeHours:0:2);
      end;
    Salaried:
      begin
        WriteLn('Type: Salaried');
        WriteLn('Annual Salary: $', Emp.AnnualSalary:0:2);
      end;
    Contract:
      begin
        WriteLn('Type: Contract');
        WriteLn('Contract Rate: $', Emp.HourlyRate:0:2);
        WriteLn('Hours Worked: ', Emp.HoursWorked:0:2);
      end;
  end;

  WriteLn;
  WriteLn('-----------------------------------------');
  WriteLn('Gross Pay:           $', Paycheck.GrossPay:10:2);
  WriteLn;
  WriteLn('Deductions:');
  WriteLn('  Federal Tax (15%): $', Paycheck.FederalTax:10:2);
  WriteLn('  State Tax (5%):    $', Paycheck.StateTax:10:2);
  WriteLn('  Social Security:   $', Paycheck.SocialSecurity:10:2);
  WriteLn('  Medicare:          $', Paycheck.Medicare:10:2);
  WriteLn('                     --------------');
  WriteLn('  Total Deductions:  $', Paycheck.TotalDeductions:10:2);
  WriteLn;
  WriteLn('=========================================');
  WriteLn('NET PAY:             $', Paycheck.NetPay:10:2);
  WriteLn('=========================================');
end;

{ Procedure to process payroll for all employees }
procedure ProcessPayroll;
var
  i: Integer;
  TotalGross, TotalNet: Real;
begin
  ClrScr;
  WriteLn('PAYROLL PROCESSING');
  WriteLn('==================');
  WriteLn;

  TotalGross := 0.0;
  TotalNet := 0.0;

  for i := 1 to EmployeeCount do
  begin
    if Employees[i].Active then
    begin
      WriteLn('Processing employee: ', Employees[i].FirstName,
              ' ', Employees[i].LastName);

      { Calculate paycheck values }
      with Employees[i] do
      begin
        TotalGross := TotalGross + CalculateGrossPay(Employees[i]);
      end;
    end;
  end;

  WriteLn;
  WriteLn('Total Gross Payroll: $', TotalGross:0:2);
  WriteLn;
  WriteLn('Payroll processing complete!');
end;

{ Procedure to initialize sample data }
procedure InitializeSampleData;
begin
  EmployeeCount := 5;

  { Employee 1 - Hourly }
  with Employees[1] do
  begin
    EmployeeID := 1001;
    FirstName := 'John';
    LastName := 'Smith';
    Department := 'Manufacturing';
    EmpType := Hourly;
    HourlyRate := 18.50;
    HoursWorked := 40.0;
    OvertimeHours := 5.0;
    Active := True;
  end;

  { Employee 2 - Salaried }
  with Employees[2] do
  begin
    EmployeeID := 1002;
    FirstName := 'Sarah';
    LastName := 'Johnson';
    Department := 'Engineering';
    EmpType := Salaried;
    AnnualSalary := 75000.0;
    Active := True;
  end;

  { Employee 3 - Hourly }
  with Employees[3] do
  begin
    EmployeeID := 1003;
    FirstName := 'Michael';
    LastName := 'Williams';
    Department := 'Warehouse';
    EmpType := Hourly;
    HourlyRate := 15.75;
    HoursWorked := 38.5;
    OvertimeHours := 0.0;
    Active := True;
  end;

  { Employee 4 - Contract }
  with Employees[4] do
  begin
    EmployeeID := 1004;
    FirstName := 'Lisa';
    LastName := 'Brown';
    Department := 'IT';
    EmpType := Contract;
    HourlyRate := 65.00;
    HoursWorked := 30.0;
    Active := True;
  end;

  { Employee 5 - Salaried }
  with Employees[5] do
  begin
    EmployeeID := 1005;
    FirstName := 'David';
    LastName := 'Davis';
    Department := 'Management';
    EmpType := Salaried;
    AnnualSalary := 95000.0;
    Active := True;
  end;
end;

{ Main program }
var
  Choice: Char;
  EmpID: Integer;
  i, FoundIndex: Integer;

begin
  InitializeSampleData;

  repeat
    ClrScr;
    WriteLn('PAYROLL SYSTEM MENU');
    WriteLn('===================');
    WriteLn;
    WriteLn('1. Generate Individual Paycheck');
    WriteLn('2. Process Full Payroll');
    WriteLn('3. List All Employees');
    WriteLn('Q. Quit');
    WriteLn;
    Write('Enter choice: ');
    Choice := ReadKey;
    WriteLn(Choice);

    case UpCase(Choice) of
      '1':
        begin
          WriteLn;
          Write('Enter Employee ID: ');
          ReadLn(EmpID);

          FoundIndex := -1;
          for i := 1 to EmployeeCount do
          begin
            if (Employees[i].EmployeeID = EmpID) and
               (Employees[i].Active) then
            begin
              FoundIndex := i;
              Break;
            end;
          end;

          if FoundIndex > 0 then
          begin
            GeneratePaycheck(Employees[FoundIndex]);
            WriteLn;
            Write('Press any key...');
            ReadKey;
          end
          else
          begin
            WriteLn('Employee not found!');
            Write('Press any key...');
            ReadKey;
          end;
        end;

      '2':
        begin
          ProcessPayroll;
          WriteLn;
          Write('Press any key...');
          ReadKey;
        end;

      '3':
        begin
          ClrScr;
          WriteLn('EMPLOYEE ROSTER');
          WriteLn('===============');
          WriteLn;
          WriteLn('ID     Name                   Department        Type');
          WriteLn('------ ---------------------- ----------------- --------');

          for i := 1 to EmployeeCount do
          begin
            if Employees[i].Active then
            begin
              Write(Employees[i].EmployeeID:6, ' ');
              Write(Employees[i].FirstName, ' ', Employees[i].LastName:20, ' ');
              Write(Employees[i].Department:17, ' ');

              case Employees[i].EmpType of
                Hourly: WriteLn('Hourly');
                Salaried: WriteLn('Salaried');
                Contract: WriteLn('Contract');
              end;
            end;
          end;

          WriteLn;
          Write('Press any key...');
          ReadKey;
        end;
    end;

  until UpCase(Choice) = 'Q';

  ClrScr;
  WriteLn('Payroll system terminated.');
end.
