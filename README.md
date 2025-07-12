# ITS Example Templates

This repository contains example templates and test cases for the [Instruction Template Specification (ITS)](https://alexanderparker.github.io/instruction-template-specification/). These can be used to validate the functionality, security, and error handling of ITS (Instruction Template Specification) compilers, including:

- [ITS Compiler (JavaScript)](https://github.com/AlexanderParker/its-compiler-js).
- [ITS Compiler (Python)](https://github.com/AlexanderParker/its-compiler-python).

## Structure

```
v1/
├── templates/           # Valid test templates
├── templates/invalid/   # Invalid templates for error testing
├── templates/security/  # Malicious templates for security testing
└── variables/          # Test variable files
```

### Valid Templates

These templates are valid and should compile normally.

| Template                             | Category        | Description                                                              |
| ------------------------------------ | --------------- | ------------------------------------------------------------------------ |
| `01-text-only.json`                  | Functional Test | Basic template with no placeholders                                      |
| `02-single-placeholder.json`         | Functional Test | Single placeholder with schema loading                                   |
| `03-multiple-placeholders.json`      | Functional Test | Multiple instruction types                                               |
| `04-simple-variables.json`           | Functional Test | Variable substitution with ${variable} syntax                            |
| `05-complex-variables.json`          | Functional Test | Object properties and array access                                       |
| `06-simple-conditionals.json`        | Functional Test | Basic conditional logic                                                  |
| `07-complex-conditionals.json`       | Functional Test | Complex conditional expressions                                          |
| `08-custom-types.json`               | Functional Test | Custom instruction type definitions                                      |
| `09-array-usage.json`                | Functional Test | Full arrays and array properties in templates                            |
| `10-comprehensive-conditionals.json` | Functional Test | All conditional operators: unary, binary, in/not in, chained comparisons |

### Invalid Templates

These templates are invalid and should trigger errors in the compiler.

| Template                                     | Category        | Description                                          |
| -------------------------------------------- | --------------- | ---------------------------------------------------- |
| `invalid/01-invalid-json.json`               | Validation Test | Template with invalid JSON syntax                    |
| `invalid/02-missing-required-fields.json`    | Validation Test | Template missing required version and content fields |
| `invalid/03-undefined-variables.json`        | Validation Test | Template with undefined variable references          |
| `invalid/04-unknown-instruction-type.json`   | Validation Test | Template with non-existent instruction type          |
| `invalid/05-invalid-conditional.json`        | Validation Test | Template with invalid conditional expression         |
| `invalid/06-missing-placeholder-config.json` | Validation Test | Placeholder missing required description config      |
| `invalid/07-empty-content.json`              | Validation Test | Template with empty content array                    |

### Security Templates

These templates include various mock security exploits which compilers should prevent.

| Template                              | Category      | Description                                          |
| ------------------------------------- | ------------- | ---------------------------------------------------- |
| `security/malicious_injection.json`   | Security Test | Template with various XSS and injection attempts     |
| `security/malicious_expressions.json` | Security Test | Conditional expressions with code injection attempts |
| `security/malicious_variables.json`   | Security Test | Variables with prototype pollution and XSS attempts  |
| `security/malicious_schema.json`      | Security Test | Schema URLs attempting SSRF and file access          |

## Variables

These files contain variables which test different variable-dependent functionality when compiling templates.

| File                                 | Description                                                 |
| ------------------------------------ | ----------------------------------------------------------- |
| `custom-variables.json`              | Custom variable values for testing variable substitution    |
| `conditional-test-variables.json`    | Variables for testing conditional logic (inverted booleans) |
| `conditional-minimal-variables.json` | Minimal variables for testing edge cases                    |
| `complex-conditional-variables.json` | Variables for testing complex conditional expressions       |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.