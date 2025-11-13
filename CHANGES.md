# Modifications for Course Project

This document describes the modifications made to the SIPssert Testing Framework for automated SIP testing.

## Overview

This modified version extends the original SIPssert framework with new task types, enhanced network management, improved logging capabilities, and additional test scenarios for SIP registration testing.

## Author

- Ruby (@ruby510054)

## Major Changes

### 1. New Task Types

Added support for additional testing components:

- **Python Task** (`sipssert/tasks/python.py`)
  - Generic Python script execution task
  - Allows custom Python-based test logic

- **Linphone Task** (`sipssert/tasks/linphone.py`)
  - Support for Linphone SIP client
  - Runs as daemon by default
  - Enables real SIP client testing

- **DNSmasq Task** (`sipssert/tasks/dnsmasq.py`)
  - DNS server support for testing scenarios
  - Runs as daemon by default
  - Facilitates domain name resolution in test environments

### 2. Test Suite Development

Created comprehensive SIP registration test suite:

- **Test Set**: `Testset/Register/`
  - `01.re-register/` - Tests SIP re-registration scenarios
  - `02.unregister/` - Tests SIP unregister functionality
  - Custom OpenSIPS configuration for registration testing
  - Python-based test steps and utilities

- **Testing Utilities** (`Testset/Register/utils_toolbox.py`)
  - Copy and remove toolbox functionality
  - Helper functions for test automation
  - 200+ lines of utility code for test scenarios

### 3. Core Framework Enhancements

#### Network Management
- Only create Docker networks if they don't already exist (prevents conflicts)
- Improved network isolation and management
- Support for workdir group DNS mode settings

#### Logging and Debugging
- PCAP file generation moved to log directory during test execution
- Better organization of network traces
- Enhanced error handling when stopping tracer

#### Container Management
- Use user UID instead of root in containers (improved security)
- Support for tasks running in daemon mode
- Better container lifecycle management

#### Path Handling
- Normalize relative paths to absolute paths
- Improved handling of scenario file paths
- Better cross-platform compatibility

#### MySQL Task Improvements
- Modified to support database extraction from tar archives
- Enhanced database initialization workflow

### 4. Main Entry Point

Added `sipssert/__main__.py` for improved package execution:
- Enables running as `python -m sipssert`
- Better integration with Python tooling

### 5. Makefile

Added `Makefile` for common development tasks:
- Simplified build and test commands
- Easier development workflow

### 6. Configuration Files

- `hosts` - Custom host mappings for test scenarios
- `linphonerc_1` - Linphone client configuration
- Updated `run.yml` with project-specific settings

## Commit History

The modifications were implemented through the following commits:

1. `79c2ebc` - Remove too large file
2. `6088873` - Add simple testcases re-register and unregister, add copy and remove toolbox feature, modify log message
3. `176d9c1` - Add main, create network only if network not exist, move pcap generate during test to log, add workdir group dns mode setting, normalize path when path is relative path, use user uid instead of root in container, add task that run in daemon, add error handling when stopping tracer
4. `93787d3` - Modify mysql task to untar database, add dnsmasq, linphone, python task

## Files Added/Modified

### New Files
- `Testset/Register/` - Complete test suite
- `sipssert/tasks/python.py` - Python task implementation
- `sipssert/tasks/linphone.py` - Linphone task implementation
- `sipssert/tasks/dnsmasq.py` - DNSmasq task implementation
- `sipssert/__main__.py` - Main entry point
- `Makefile` - Build automation
- `hosts` - Host mappings
- `linphonerc_1` - Linphone configuration

### Modified Files
- `sipssert/task.py` - Enhanced task functionality
- `sipssert/scenario.py` - Improved scenario handling
- `sipssert/network/bridged.py` - Network management updates
- `sipssert/tasks/mysql.py` - Database extraction support
- `sipssert/tasks_list.py` - New task type registration
- `sipssert/tests_set.py` - Test set enhancements
- `sipssert/tracer.py` - Improved tracing and logging

## Usage

The modified framework maintains backward compatibility with the original SIPssert. New features can be used by:

1. Using new task types in scenario YAML files:
```yaml
tasks:
  - name: DNS Server
    type: dnsmasq

  - name: SIP Client
    type: linphone

  - name: Custom Test
    type: python
```

2. Running the registration test suite:
```bash
sipssert Testset/Register
```

3. Building with Makefile:
```bash
make build
make test
```

## Upstream Compatibility

This fork is based on the original SIPssert Testing Framework. The modifications are designed to be additive and maintain compatibility with existing test scenarios. The base functionality remains unchanged.

## License

Modifications maintain the same license as the original project:
- Source code: GNU General Public License v3.0
- Documentation: Creative Commons License 4.0

---

For the original SIPssert documentation, see [README.md](README.md).
