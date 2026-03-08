"""Tests for agent.tools"""
import pytest
from agent.tools import calculator, word_count, run_tool, REGISTRY


class TestCalculator:
    def test_addition(self):
        assert calculator(expression="2+2") == "4"

    def test_multiplication(self):
        assert calculator(expression="3*7") == "21"

    def test_float(self):
        result = calculator(expression="10/4")
        assert result == "2.5"

    def test_sqrt(self):
        result = calculator(expression="sqrt(16)")
        assert result == "4.0"

    def test_power(self):
        result = calculator(expression="2**10")
        assert result == "1024"

    def test_division_by_zero(self):
        result = calculator(expression="1/0")
        assert "division by zero" in result.lower()

    def test_disallowed_chars(self):
        result = calculator(expression="__import__('os')")
        assert "disallowed" in result.lower()

    def test_pi(self):
        import math
        result = float(calculator(expression="pi"))
        assert abs(result - math.pi) < 1e-10


class TestWordCount:
    def test_basic(self):
        result = word_count(text="hello world")
        assert "Words: 2" in result
        assert "Characters: 11" in result

    def test_empty(self):
        result = word_count(text="")
        assert "Words: 0" in result


class TestRunTool:
    def test_known_tool(self):
        result = run_tool("calculator", expression="1+1")
        assert result == "2"

    def test_unknown_tool(self):
        result = run_tool("nonexistent")
        assert "Unknown tool" in result

    def test_registry_contains_expected_tools(self):
        for name in ("calculator", "word_count", "help"):
            assert name in REGISTRY
