{ INVENTORY.PAS - Warehouse Inventory Management System }
{ Legacy Turbo Pascal code from 1990s retail system }
{ Manages product stock, orders, and reorder alerts }

program InventorySystem;

uses
  Crt, Dos;

const
  MaxProducts = 1000;
  ReorderThreshold = 10;
  DatabaseFile = 'INVENTORY.DAT';

type
  ProductRecord = record
    ProductID: string[10];
    ProductName: string[50];
    Category: string[20];
    Quantity: Integer;
    ReorderLevel: Integer;
    UnitCost: Real;
    UnitPrice: Real;
    SupplierID: string[10];
    LastUpdated: string[10];
    Active: Boolean;
  end;

  InventoryArray = array[1..MaxProducts] of ProductRecord;

var
  Inventory: InventoryArray;
  ProductCount: Integer;
  Choice: Char;

{ Procedure to initialize inventory database }
procedure InitializeInventory(var Inv: InventoryArray; var Count: Integer);
var
  i: Integer;
begin
  Count := 0;
  for i := 1 to MaxProducts do
  begin
    Inv[i].ProductID := '';
    Inv[i].Quantity := 0;
    Inv[i].Active := False;
  end;
end;

{ Function to find product by ID }
function FindProduct(const Inv: InventoryArray; Count: Integer;
                     ID: string): Integer;
var
  i: Integer;
begin
  FindProduct := -1;
  for i := 1 to Count do
  begin
    if (Inv[i].ProductID = ID) and (Inv[i].Active) then
    begin
      FindProduct := i;
      Exit;
    end;
  end;
end;

{ Procedure to add new product }
procedure AddProduct(var Inv: InventoryArray; var Count: Integer);
var
  NewProduct: ProductRecord;
begin
  if Count >= MaxProducts then
  begin
    WriteLn('ERROR: Inventory database full!');
    Exit;
  end;

  ClrScr;
  WriteLn('ADD NEW PRODUCT');
  WriteLn('===============');
  WriteLn;

  Write('Product ID: ');
  ReadLn(NewProduct.ProductID);

  { Check for duplicate }
  if FindProduct(Inv, Count, NewProduct.ProductID) <> -1 then
  begin
    WriteLn('ERROR: Product ID already exists!');
    Exit;
  end;

  Write('Product Name: ');
  ReadLn(NewProduct.ProductName);
  Write('Category: ');
  ReadLn(NewProduct.Category);
  Write('Initial Quantity: ');
  ReadLn(NewProduct.Quantity);
  Write('Reorder Level: ');
  ReadLn(NewProduct.ReorderLevel);
  Write('Unit Cost: $');
  ReadLn(NewProduct.UnitCost);
  Write('Unit Price: $');
  ReadLn(NewProduct.UnitPrice);
  Write('Supplier ID: ');
  ReadLn(NewProduct.SupplierID);

  NewProduct.Active := True;
  NewProduct.LastUpdated := '2024-01-15';

  Inc(Count);
  Inv[Count] := NewProduct;

  WriteLn;
  WriteLn('Product added successfully!');
end;

{ Procedure to update stock quantity }
procedure UpdateStock(var Inv: InventoryArray; Count: Integer);
var
  ProductID: string[10];
  Index, Delta: Integer;
  TransType: Char;
begin
  ClrScr;
  WriteLn('UPDATE STOCK QUANTITY');
  WriteLn('====================');
  WriteLn;

  Write('Product ID: ');
  ReadLn(ProductID);

  Index := FindProduct(Inv, Count, ProductID);
  if Index = -1 then
  begin
    WriteLn('ERROR: Product not found!');
    Exit;
  end;

  WriteLn('Product: ', Inv[Index].ProductName);
  WriteLn('Current Quantity: ', Inv[Index].Quantity);
  WriteLn;
  WriteLn('Transaction Type:');
  WriteLn('  (R)eceive shipment');
  WriteLn('  (S)ale/Issue');
  WriteLn('  (A)djustment');
  Write('Choice: ');
  ReadLn(TransType);

  Write('Quantity: ');
  ReadLn(Delta);

  case UpCase(TransType) of
    'R': Inv[Index].Quantity := Inv[Index].Quantity + Delta;
    'S': begin
           if Inv[Index].Quantity >= Delta then
             Inv[Index].Quantity := Inv[Index].Quantity - Delta
           else
           begin
             WriteLn('ERROR: Insufficient stock!');
             Exit;
           end;
         end;
    'A': Inv[Index].Quantity := Delta;
  else
    WriteLn('ERROR: Invalid transaction type!');
    Exit;
  end;

  WriteLn;
  WriteLn('Stock updated. New quantity: ', Inv[Index].Quantity);

  { Check reorder level }
  if Inv[Index].Quantity <= Inv[Index].ReorderLevel then
  begin
    WriteLn;
    WriteLn('*** REORDER ALERT ***');
    WriteLn('Product is below reorder level!');
    WriteLn('Recommended order quantity: ',
            Inv[Index].ReorderLevel * 2 - Inv[Index].Quantity);
  end;
end;

{ Procedure to display inventory report }
procedure DisplayInventory(const Inv: InventoryArray; Count: Integer);
var
  i: Integer;
  TotalValue: Real;
begin
  ClrScr;
  WriteLn('INVENTORY REPORT');
  WriteLn('=================');
  WriteLn;
  WriteLn('ID         Name                      Qty    Cost      Value     Status');
  WriteLn('---------- ------------------------- ------ --------- --------- --------');

  TotalValue := 0.0;

  for i := 1 to Count do
  begin
    if Inv[i].Active then
    begin
      Write(Inv[i].ProductID:10, ' ');
      Write(Inv[i].ProductName:25, ' ');
      Write(Inv[i].Quantity:6, ' ');
      Write(Inv[i].UnitCost:9:2, ' ');
      Write((Inv[i].Quantity * Inv[i].UnitCost):9:2, ' ');

      if Inv[i].Quantity <= Inv[i].ReorderLevel then
        WriteLn('LOW')
      else
        WriteLn('OK');

      TotalValue := TotalValue + (Inv[i].Quantity * Inv[i].UnitCost);
    end;
  end;

  WriteLn('---------- ------------------------- ------ --------- --------- --------');
  WriteLn('Total Inventory Value: $', TotalValue:12:2);
end;

{ Main menu procedure }
procedure ShowMenu;
begin
  ClrScr;
  WriteLn('WAREHOUSE INVENTORY SYSTEM');
  WriteLn('==========================');
  WriteLn;
  WriteLn('1. Add New Product');
  WriteLn('2. Update Stock Quantity');
  WriteLn('3. Display Inventory Report');
  WriteLn('4. Search Product');
  WriteLn('5. Reorder Report');
  WriteLn('Q. Quit');
  WriteLn;
  Write('Enter choice: ');
end;

{ Main program }
begin
  InitializeInventory(Inventory, ProductCount);

  { Load sample data }
  ProductCount := 3;
  with Inventory[1] do
  begin
    ProductID := 'PROD001';
    ProductName := 'Office Chair Deluxe';
    Category := 'Furniture';
    Quantity := 25;
    ReorderLevel := 10;
    UnitCost := 89.99;
    UnitPrice := 149.99;
    SupplierID := 'SUP100';
    Active := True;
  end;

  with Inventory[2] do
  begin
    ProductID := 'PROD002';
    ProductName := 'Printer Paper (Ream)';
    Category := 'Office Supplies';
    Quantity := 5;
    ReorderLevel := 20;
    UnitCost := 4.99;
    UnitPrice := 8.99;
    SupplierID := 'SUP101';
    Active := True;
  end;

  with Inventory[3] do
  begin
    ProductID := 'PROD003';
    ProductName := 'Wireless Mouse';
    Category := 'Electronics';
    Quantity := 45;
    ReorderLevel := 15;
    UnitCost := 12.50;
    UnitPrice := 24.99;
    SupplierID := 'SUP102';
    Active := True;
  end;

  { Main loop }
  repeat
    ShowMenu;
    Choice := ReadKey;
    case UpCase(Choice) of
      '1': AddProduct(Inventory, ProductCount);
      '2': UpdateStock(Inventory, ProductCount);
      '3': DisplayInventory(Inventory, ProductCount);
      'Q': WriteLn('Exiting system...');
    end;

    if UpCase(Choice) <> 'Q' then
    begin
      WriteLn;
      Write('Press any key to continue...');
      ReadKey;
    end;
  until UpCase(Choice) = 'Q';

  ClrScr;
  WriteLn('System shutdown complete.');
end.
