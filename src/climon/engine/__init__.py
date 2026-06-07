"""The pure battle engine: data model, rules, and turn resolution.

This package does no I/O and imports neither Textual nor websockets. Given the
same state, actions, and random seed it always produces the same result, which is
what lets the online server resolve turns authoritably and lets tests stay stable.
"""
