---
type: "always_apply"
---

# LRC Toolbox Development Rules and Guidelines

## 📋 Overview

This document establishes the development rules and guidelines for the LRC Toolbox v2.0 enhanced template management system. These rules ensure consistent, quality development while following the UI-first approach outlined in the implementation plan.

## 🎯 Core Development Principles

### 1. Always Ask to Confirm Before Changing Specifications
- **RULE**: Never modify specifications, requirements, or architectural decisions without explicit user confirmation
- **Process**: 
  1. Identify any proposed changes to existing specs
  2. Present the change with clear rationale
  3. Wait for explicit user approval before proceeding
  4. Document the approved change in relevant specification files
- **Examples of Changes Requiring Confirmation**:
  - Modifying UI layout or workflow
  - Changing API signatures or data structures
  - Altering directory structure or file organization
  - Adding or removing features from requirements
  - Changing development approach or timeline

### 2. Implement One Task at a Time
- **RULE**: Follow the task breakdown in `task.md` sequentially, completing one task fully before starting the next
- **Process**:
  1. Reference the specific task number (e.g., TASK-001)
  2. Review task dependencies and ensure they are completed
  3. Implement according to acceptance criteria
  4. Test the implementation
  5. Mark task as complete before proceeding
- **Task Tracking**: Update task status in `task.md` or maintain separate progress tracking
- **No Parallel Tasks**: Complete current task fully before starting next task

### 3. Research First, Then Implement
- **RULE**: Always research and understand requirements thoroughly before writing code
- **Research Process**:
  1. **Analyze Existing Code**: Study `maya/mockup/lrc_manager.py` for current functionality
  2. **Review Specifications**: Check `ui_design.md`, `user_journey.md`, and `implement_plan.md`
  3. **Understand Context**: Review related tasks and dependencies
  4. **Plan Implementation**: Outline approach before coding
  5. **Verify Understanding**: Ask clarifying questions if requirements are unclear
- **Documentation**: Document research findings and implementation decisions

### 4. Always Remove Unused Tests, Debug Scripts, and Temporary Files
- **RULE**: Clean up all temporary, debug, and unused files before committing
- **Cleanup Checklist**:
  - [ ] Remove debug print statements and temporary logging
  - [ ] Delete test scripts created for development/debugging
  - [ ] Remove commented-out code blocks
  - [ ] Clean up temporary files and directories
  - [ ] Remove unused imports and variables
  - [ ] Delete placeholder files that are no longer needed
- **Before Each Commit**: Run cleanup verification
- **File Types to Remove**:
  - `test_*.py` files created for debugging (not official tests)
  - `debug_*.py` or `temp_*.py` files
  - `.tmp`, `.bak`, `.old` files
  - Unused configuration or setup files

### 5. Always Update Documentation When Specifications Change
- **RULE**: Keep all documentation synchronized with implementation changes
- **Documentation Update Process**:
  1. **Identify Impact**: Determine which documents are affected by changes
  2. **Update Specifications**: Modify relevant `.md` files in `.plan/` directory
  3. **Update Code Documentation**: Ensure docstrings match implementation
  4. **Update README**: Reflect any user-facing changes
  5. **Version Documentation**: Note changes in commit messages
- **Documents to Maintain**:
  - `implement_plan.md` - Architecture and approach changes
  - `ui_design.md` - UI layout and interaction changes
  - `task.md` - Task completion status and modifications
  - `user_journey.md` - Workflow changes
  - `README.md` - User-facing feature changes
  - Code docstrings and inline documentation

### 6. Ask for Clarification When Prompts Are Not Clear
- **RULE**: Never guess or assume requirements when instructions are ambiguous
- **Clarification Process**:
  1. **Identify Ambiguity**: Clearly state what is unclear
  2. **Ask Specific Questions**: Request specific clarification, not general guidance
  3. **Provide Context**: Reference relevant specifications or previous discussions
  4. **Wait for Response**: Do not proceed with implementation until clarification is received
  5. **Document Clarification**: Update relevant documentation with clarified requirements
- **Examples of When to Ask**:
  - Conflicting requirements between documents
  - Unclear user interface behavior
  - Ambiguous technical specifications
  - Missing implementation details
  - Uncertain priority or scope

## 🏗️ Implementation Guidelines

### UI-First Development Approach
- **Priority Order**: UI components → Placeholder backends → Real backends
- **Placeholder Strategy**: Create realistic mock data and responses
- **Integration Testing**: Ensure UI works with placeholders before implementing real backends
- **User Feedback**: Gather feedback on UI before backend complexity

### Code Quality Standards
- **Formatting**: Use Black formatter (line length: 88)
- **Linting**: Pass flake8 checks
- **Documentation**: Google-style docstrings for all functions and classes
- **Testing**: Minimum 80% test coverage for real implementations
- **Type Hints**: Use type hints where appropriate

### File Organization
- **Module Structure**: Follow the defined architecture in `implement_plan.md`
- **Import Organization**: Use relative imports within package, absolute for external
- **Naming Conventions**: Follow Python PEP 8 naming conventions
- **File Headers**: Include module docstrings with purpose and usage

### Git Workflow
- **Branch Strategy**: Work on `feature/ui-first-implementation` branch
- **Commit Messages**: Clear, descriptive messages referencing task numbers
- **Commit Frequency**: Commit after each completed task
- **Clean History**: Squash commits if necessary before merging

## 🧪 Testing and Quality Assurance

### Testing Strategy
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **UI Tests**: Test widget functionality and user interactions
- **Maya Tests**: Test Maya API integration (when implemented)

### Quality Checks Before Commit
1. **Code Formatting**: Run `black maya/lrc_toolbox/`
2. **Linting**: Run `flake8 maya/lrc_toolbox/`
3. **Tests**: Run `pytest` and ensure all tests pass
4. **Documentation**: Verify docstrings are complete and accurate
5. **Cleanup**: Remove all temporary and debug files
6. **Functionality**: Test that implemented features work as expected

## 📋 Task Management

### Task Execution Process
1. **Select Next Task**: Choose next task from `task.md` based on dependencies
2. **Research Phase**: Study requirements and existing code
3. **Plan Implementation**: Outline approach and identify potential issues
4. **Implement**: Write code following quality standards
5. **Test**: Verify implementation meets acceptance criteria
6. **Document**: Update relevant documentation
7. **Cleanup**: Remove temporary files and debug code
8. **Commit**: Commit changes with clear message
9. **Update Status**: Mark task as complete

### Progress Tracking
- **Task Status**: Track completion in `task.md` or separate tracking system
- **Dependencies**: Verify all dependencies are met before starting task
- **Blockers**: Identify and resolve blockers promptly
- **Time Tracking**: Monitor actual time vs. estimated time for future planning

## 🚨 Error Handling and Recovery

### When Things Go Wrong
1. **Stop Implementation**: Don't continue if errors or issues arise
2. **Analyze Problem**: Understand root cause of issue
3. **Consult Documentation**: Check specifications and previous decisions
4. **Ask for Help**: Request clarification or guidance if needed
5. **Document Issue**: Record problem and solution for future reference

### Rollback Strategy
- **Git History**: Use git to revert problematic changes
- **Backup Strategy**: Maintain working versions at key milestones
- **Testing**: Verify rollback doesn't break existing functionality

## 📞 Communication and Collaboration

### Status Updates
- **Regular Updates**: Provide progress updates on task completion
- **Issue Reporting**: Report blockers or issues promptly
- **Clarification Requests**: Ask questions when requirements are unclear
- **Change Proposals**: Present proposed changes with clear rationale

### Documentation Standards
- **Clear Writing**: Use clear, concise language in all documentation
- **Consistent Format**: Follow established formatting conventions
- **Version Control**: Track changes to documentation
- **Accessibility**: Ensure documentation is easy to understand and navigate

---

## 📝 Summary Checklist

Before any implementation work:
- [ ] Confirm specifications and requirements are clear
- [ ] Identify specific task from `task.md`
- [ ] Research existing code and documentation
- [ ] Plan implementation approach
- [ ] Verify all dependencies are met

During implementation:
- [ ] Follow code quality standards
- [ ] Write tests for new functionality
- [ ] Document code with proper docstrings
- [ ] Test implementation thoroughly

Before committing:
- [ ] Remove all debug code and temporary files
- [ ] Run code formatting and linting
- [ ] Verify all tests pass
- [ ] Update relevant documentation
- [ ] Write clear commit message

**Remember**: When in doubt, ask for clarification rather than making assumptions!
