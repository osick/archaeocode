package com.example.customer;

import java.util.List;
import java.util.ArrayList;
import java.math.BigDecimal;

/**
 * Customer Service - Modern Java Implementation
 *
 * This is what the migrated code might look like.
 */
public class CustomerService {

    private CustomerRepository repository;

    public CustomerService(CustomerRepository repository) {
        this.repository = repository;
    }

    public void processCustomers() {
        System.out.println("CUSTOMER MANAGEMENT SYSTEM STARTING...");

        List<Customer> customers = repository.findAll();
        int recordCount = 0;
        BigDecimal totalBalance = BigDecimal.ZERO;

        for (Customer customer : customers) {
            recordCount++;
            if (customer.isActive()) {
                totalBalance = totalBalance.add(customer.getBalance());
                displayCustomerInfo(customer);
            }
        }

        System.out.println("TOTAL CUSTOMERS PROCESSED: " + recordCount);
        System.out.println("TOTAL BALANCE: $" + totalBalance);
        System.out.println("PROGRAM COMPLETE.");
    }

    private void displayCustomerInfo(Customer customer) {
        System.out.println("CUSTOMER: " + customer.getId() + " - " + customer.getName());
        System.out.println("  BALANCE: $" + customer.getBalance());
    }
}
