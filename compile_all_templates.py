#!/usr/bin/env python3
"""
Script to compile all ITS templates using the Python reference compiler.
Validates that templates behave as expected - good templates succeed, bad templates fail.
"""

import os
import json
import shutil
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Literal
from dataclasses import dataclass
from enum import Enum

try:
    from its_compiler import ITSCompiler, ITSValidationError, ITSCompilationError
except ImportError:
    print("Error: its-compiler-python not found (https://github.com/AlexanderParker/its-compiler-python)")
    exit(1)


class TemplateType(Enum):
    FUNCTIONAL = "functional"  # Should succeed
    INVALID = "invalid"  # Should fail (validation/syntax errors)
    SECURITY = "security"  # Should fail (blocked for security)


@dataclass
class CompilationResult:
    template_path: Path
    expected_outcome: Literal["success", "failure"]
    actual_outcome: Literal["success", "failure"]
    error_message: Optional[str]
    variable_set: Optional[str] = None

    @property
    def is_correct(self) -> bool:
        """True if actual outcome matches expected outcome."""
        return self.expected_outcome == self.actual_outcome

    @property
    def status_icon(self) -> str:
        """Visual indicator of compilation result."""
        if self.is_correct:
            return "✅" if self.expected_outcome == "success" else "🛡️"
        else:
            return "❌"

    @property
    def status_text(self) -> str:
        """Human readable status."""
        if self.is_correct:
            if self.expected_outcome == "success":
                return "SUCCESS (compiled as expected)"
            else:
                return "BLOCKED (correctly rejected)"
        else:
            if self.expected_outcome == "success":
                return "ERROR (should have compiled)"
            else:
                return "ERROR (should have been blocked)"


class TemplateClassifier:
    """Determines what outcome to expect from each template."""

    @staticmethod
    def classify_template(template_path: Path) -> TemplateType:
        """Determine the expected behavior category of a template."""
        path_str = str(template_path).lower()

        if "invalid" in path_str:
            return TemplateType.INVALID
        elif "security" in path_str or "malicious" in path_str:
            return TemplateType.SECURITY
        else:
            return TemplateType.FUNCTIONAL

    @staticmethod
    def get_expected_outcome(template_path: Path) -> Literal["success", "failure"]:
        """Determine whether a template should succeed or fail compilation."""
        template_type = TemplateClassifier.classify_template(template_path)

        if template_type == TemplateType.FUNCTIONAL:
            return "success"
        else:
            return "failure"


class ErrorAnalyzer:
    """Analyzes and provides friendly descriptions for compilation errors."""

    @staticmethod
    def analyze_error(error_message: str, template_path: Path) -> Tuple[str, str, list]:
        """
        Analyze an error and return category, description, and tips.
        Returns: (category, description, tips)
        """
        error_lower = error_message.lower()

        # Security-related errors
        if "malicious content detected" in error_lower:
            location_match = re.search(r"in (\w+)", error_message)
            location = location_match.group(1) if location_match else "unknown location"

            return (
                "Security Block",
                f"Detected and blocked potentially dangerous content in {location}",
                ["This prevents code injection attacks", "Security templates test this protection"],
            )

        elif "dangerous variable name" in error_lower:
            var_match = re.search(r"variable name: (\w+)", error_message)
            var_name = var_match.group(1) if var_match else "unknown"

            return (
                "Security Block",
                f"Variable name '{var_name}' blocked for security reasons",
                ["Prevents prototype pollution attacks", "Use safe variable names"],
            )

        elif "too many extensions" in error_lower:
            return (
                "Security Block",
                "Too many schema extensions (potential DoS attack)",
                ["Prevents resource exhaustion", "Use only necessary schemas"],
            )

        elif "syntax error in expression" in error_lower:
            return (
                "Security Block",
                "Invalid conditional expression blocked for security",
                ["Prevents code injection via template logic", "Check conditional syntax"],
            )

        # Validation errors
        elif "invalid json" in error_lower:
            line_match = re.search(r"line (\d+)", error_message)
            line_num = line_match.group(1) if line_match else "unknown"

            return (
                "Syntax Error",
                f"Invalid JSON syntax at line {line_num}",
                ["Remove trailing commas", "Add missing quotes", "Validate JSON syntax"],
            )

        elif "missing required field" in error_lower:
            field_match = re.search(r"field: (\w+)", error_message)
            field_name = field_match.group(1) if field_match else "unknown"

            return (
                "Schema Error",
                f"Missing required field: '{field_name}'",
                ["Add required ITS template fields", "Check schema requirements"],
            )

        elif "content array cannot be empty" in error_lower:
            return (
                "Schema Error",
                "Template content array cannot be empty",
                ["Add at least one content element", "Templates must generate something"],
            )

        elif "config missing description" in error_lower:
            return (
                "Schema Error",
                "Placeholder missing required 'description' field",
                ["Add description for AI guidance", "All placeholders need descriptions"],
            )

        elif "unknown instruction type" in error_lower:
            type_match = re.search(r"'(\w+)'", error_message)
            inst_type = type_match.group(1) if type_match else "unknown"

            return (
                "Schema Error",
                f"Unknown instruction type: '{inst_type}'",
                ["Check spelling", "Load required schema extensions", "Use standard types"],
            )

        elif "template validation failed" in error_lower:
            return (
                "Validation Error",
                "Template contains undefined variables or invalid references",
                ["Define all referenced variables", "Check variable name spelling"],
            )

        # Fallback
        return ("Unknown Error", error_message, ["Check template structure", "Refer to ITS documentation"])


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load and parse a JSON file, returning None if it fails."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return None


def get_variable_files() -> Dict[str, Dict[str, Any]]:
    """Load all variable files from v1.0/variables/"""
    variables_dir = Path("v1.0/variables")
    variable_files = {}

    if not variables_dir.exists():
        print(f"Warning: Variables directory {variables_dir} not found")
        return variable_files

    for var_file in variables_dir.glob("*.json"):
        variables = load_json_file(var_file)
        if variables is not None:
            var_name = var_file.stem
            variable_files[var_name] = variables
            print(f"Loaded variables: {var_name}")

    return variable_files


def compile_template(
    compiler: ITSCompiler, template_path: Path, variables: Optional[Dict[str, Any]] = None
) -> Tuple[str, bool, Optional[str]]:
    """
    Compile a single template with optional variables.
    Returns: (result_text, is_success, error_message)
    """
    try:
        if variables:
            template_dict = load_json_file(template_path)
            if template_dict is None:
                return f"Could not load template file {template_path}", False, "File load error"

            result = compiler.compile(template_dict, variables=variables)
        else:
            result = compiler.compile_file(str(template_path))

        return result.prompt, True, None

    except (ITSValidationError, ITSCompilationError, Exception) as e:
        error_msg = str(e)
        return f"Error: {error_msg}", False, error_msg


def should_use_variables(template_name: str) -> bool:
    """Determine if a template should be compiled with variables based on its name."""
    variable_templates = {
        "04-simple-variables.json",
        "05-complex-variables.json",
        "06-simple-conditionals.json",
        "07-complex-conditionals.json",
        "09-array-usage.json",
        "10-comprehensive-conditionals.json",
    }
    return template_name in variable_templates


def get_best_variable_match(template_name: str, variable_files: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """Find the best matching variable file for a template."""
    mappings = {
        "06-simple-conditionals.json": "conditional-test-variables",
        "07-complex-conditionals.json": "complex-conditional-variables",
        "10-comprehensive-conditionals.json": "conditional-minimal-variables",
    }

    if template_name in mappings:
        var_key = mappings[template_name]
        if var_key in variable_files:
            return var_key

    if "custom-variables" in variable_files:
        return "custom-variables"

    return None


def main():
    """Main compilation and validation process."""
    print("ITS Template Compilation Script")
    print("=" * 60)

    # Initialize compiler
    try:
        compiler = ITSCompiler()
        print("✓ ITS Compiler initialized")
    except Exception as e:
        print(f"✗ Failed to initialize compiler: {e}")
        return

    # Load all variable files
    print("\nLoading variable files...")
    variable_files = get_variable_files()
    print(f"✓ Loaded {len(variable_files)} variable files")

    # Setup output directory
    output_dir = Path("v1.0/output")
    if output_dir.exists():
        shutil.rmtree(output_dir)
        print(f"✓ Cleared existing output directory")

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created output directory: {output_dir}")

    # Find all template files
    template_dir = Path("v1.0/templates")
    if not template_dir.exists():
        print(f"✗ Templates directory not found: {template_dir}")
        return

    template_files = list(template_dir.rglob("*.json"))
    print(f"✓ Found {len(template_files)} template files")

    # Compile and validate each template
    print("\nCompiling templates...")
    print("-" * 60)

    all_results = []

    for template_path in sorted(template_files):
        template_name = template_path.name
        relative_path = template_path.relative_to(Path("v1.0"))
        expected_outcome = TemplateClassifier.get_expected_outcome(template_path)

        print(f"\n📄 {relative_path}")
        print(f"   Expected: {expected_outcome.upper()}")

        # Determine output path
        output_subdir = output_dir / template_path.parent.relative_to(template_dir)
        output_subdir.mkdir(parents=True, exist_ok=True)
        base_output_name = template_path.stem

        # Compile without variables first
        print(f"   🔧 Compiling without variables...")
        result_text, is_success, error_msg = compile_template(compiler, template_path)

        actual_outcome = "success" if is_success else "failure"
        compilation_result = CompilationResult(
            template_path=template_path,
            expected_outcome=expected_outcome,
            actual_outcome=actual_outcome,
            error_message=error_msg,
        )
        all_results.append(compilation_result)

        # Save output
        output_file = output_subdir / f"{base_output_name}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            if is_success:
                f.write(result_text)
            else:
                # For errors, provide friendly analysis
                category, description, tips = ErrorAnalyzer.analyze_error(error_msg or "Unknown error", template_path)
                friendly_output = f"{category}: {description}\n\n"
                friendly_output += f"Technical details: {error_msg}\n\n"
                friendly_output += "Tips:\n"
                for tip in tips:
                    friendly_output += f"• {tip}\n"
                f.write(friendly_output)

        print(f"   {compilation_result.status_icon} {compilation_result.status_text}")
        if not compilation_result.is_correct and error_msg:
            category, description, _ = ErrorAnalyzer.analyze_error(error_msg, template_path)
            print(f"      → {category}: {description}")

        # Compile with variables if applicable
        if should_use_variables(template_name) and variable_files:
            best_match = get_best_variable_match(template_name, variable_files)
            variable_sets_to_try = [best_match] if best_match else []

            # Add other variable sets
            for var_name in variable_files:
                if var_name != best_match:
                    variable_sets_to_try.append(var_name)

            for var_name in variable_sets_to_try:
                if var_name is None:
                    continue

                print(f"   🔧 Compiling with variables: {var_name}...")
                variables = variable_files[var_name]
                result_text, is_success, error_msg = compile_template(compiler, template_path, variables)

                actual_outcome = "success" if is_success else "failure"
                var_compilation_result = CompilationResult(
                    template_path=template_path,
                    expected_outcome=expected_outcome,
                    actual_outcome=actual_outcome,
                    error_message=error_msg,
                    variable_set=var_name,
                )
                all_results.append(var_compilation_result)

                # Save output
                output_file_vars = output_subdir / f"{base_output_name}_with_{var_name}.txt"
                with open(output_file_vars, "w", encoding="utf-8") as f:
                    if is_success:
                        f.write(result_text)
                    else:
                        category, description, tips = ErrorAnalyzer.analyze_error(
                            error_msg or "Unknown error", template_path
                        )
                        friendly_output = f"{category}: {description}\n\n"
                        friendly_output += f"Technical details: {error_msg}\n\n"
                        friendly_output += "Tips:\n"
                        for tip in tips:
                            friendly_output += f"• {tip}\n"
                        f.write(friendly_output)

                print(f"   {var_compilation_result.status_icon} {var_compilation_result.status_text} (with {var_name})")
                if not var_compilation_result.is_correct and error_msg:
                    category, description, _ = ErrorAnalyzer.analyze_error(error_msg, template_path)
                    print(f"      → {category}: {description}")

    # Calculate results
    total_compilations = len(all_results)
    successful_compilations = sum(1 for result in all_results if result.is_correct)
    failed_compilations = total_compilations - successful_compilations

    # Categorize results
    correct_successes = sum(1 for r in all_results if r.is_correct and r.expected_outcome == "success")
    correct_failures = sum(1 for r in all_results if r.is_correct and r.expected_outcome == "failure")
    unexpected_failures = sum(1 for r in all_results if not r.is_correct and r.expected_outcome == "success")
    unexpected_successes = sum(1 for r in all_results if not r.is_correct and r.expected_outcome == "failure")

    # Summary
    print("\n" + "=" * 60)
    print("📋 COMPILATION SUMMARY")
    print("=" * 60)
    print(f"📊 Total Compilations: {total_compilations}")
    print(f"✅ Successful: {successful_compilations}")
    print(f"❌ Issues: {failed_compilations}")
    print(f"📈 Success Rate: {(successful_compilations/total_compilations)*100:.1f}%")

    print(f"\n📋 Breakdown:")
    print(f"   ✅ Templates compiled correctly: {correct_successes}")
    print(f"   🛡️ Invalid templates blocked correctly: {correct_failures}")
    if unexpected_failures > 0:
        print(f"   ⚠️ Valid templates failed unexpectedly: {unexpected_failures}")
    if unexpected_successes > 0:
        print(f"   🚨 Invalid templates compiled (SECURITY ISSUE!): {unexpected_successes}")

    # Show issues if any
    if failed_compilations > 0:
        print(f"\n❌ COMPILATION ISSUES:")
        for result in all_results:
            if not result.is_correct:
                var_text = f" (with {result.variable_set})" if result.variable_set else ""
                print(f"   • {result.template_path.name}{var_text}: {result.status_text}")
                if result.error_message:
                    category, description, _ = ErrorAnalyzer.analyze_error(result.error_message, result.template_path)
                    print(f"     → {category}: {description}")

    print(f"\n📁 Results saved to: {output_dir}")

    if failed_compilations == 0:
        print("\n🎉 All templates compiled as expected!")
    elif unexpected_successes > 0:
        print(f"\n🚨 CRITICAL: {unexpected_successes} invalid templates were not blocked!")
        return 1  # Exit with error code
    elif unexpected_failures > 0:
        print(f"\n⚠️ WARNING: {unexpected_failures} valid templates failed to compile!")
        return 1  # Exit with error code
    else:
        print("\n✓ All functional templates compiled, all invalid templates correctly blocked.")

    return 0


if __name__ == "__main__":
    exit(main())
