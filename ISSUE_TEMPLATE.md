# Issue Template for Auto Issue Runner

Use this template when creating issues that you want Claude Code to automatically implement. This template helps ensure Claude has all the context needed to successfully complete the task.

## Issue Title
Keep it concise and descriptive. Start with an action verb when possible:
- ✅ `Add user input validation to login form`
- ✅ `Fix memory leak in image processing function`
- ✅ `Update API documentation for user endpoints`
- ❌ `Login problems` (too vague)
- ❌ `Rewrite entire authentication system` (too large)

## Issue Description Template

```markdown
## Summary
Brief description of what needs to be done and why.

## Current Behavior
What currently happens (if this is a bug fix or modification).

## Expected Behavior
What should happen after the implementation.

## Acceptance Criteria
- [ ] Specific, testable requirement 1
- [ ] Specific, testable requirement 2
- [ ] Specific, testable requirement 3

## Implementation Notes
- Mention specific files that likely need changes
- Reference existing patterns or similar implementations
- Note any architectural constraints or preferences
- Highlight any edge cases to consider

## Related Context
- Link to related issues, PRs, or documentation
- Mention any dependencies or prerequisites
- Reference design docs or specifications if available

## Testing Notes
- Describe how the feature should be tested
- Mention specific test cases if known
- Note any manual testing steps required
```

## Good Issue Examples

### Example 1: Feature Addition
```markdown
## Summary
Add input validation to the user registration form to prevent invalid email addresses and weak passwords.

## Current Behavior
Users can submit the registration form with any input, leading to invalid accounts in the database.

## Expected Behavior
Form should validate email format and password strength before submission, showing helpful error messages.

## Acceptance Criteria
- [ ] Email field validates proper email format (contains @ and valid domain)
- [ ] Password must be at least 8 characters with one number and one special character
- [ ] Error messages appear below each field when validation fails
- [ ] Form cannot be submitted until all validations pass
- [ ] Existing tests continue to pass

## Implementation Notes
- Use the existing validation utility in `src/utils/validation.js`
- Follow the error message patterns from the login form in `src/components/LoginForm.js`
- The registration form is in `src/components/RegisterForm.js`
- Consider using the same CSS classes as other form validations for consistency

## Testing Notes
- Test with various invalid email formats (missing @, invalid domains)
- Test with weak passwords (too short, no numbers, no special chars)
- Verify error messages display correctly
- Ensure form submission is properly blocked/allowed
```

### Example 2: Bug Fix
```markdown
## Summary
Fix the memory leak that occurs when processing large images in the thumbnail generation service.

## Current Behavior
Memory usage continuously increases when processing multiple large images, eventually causing the service to crash.

## Expected Behavior
Memory should be properly released after each image is processed, maintaining stable memory usage.

## Acceptance Criteria
- [ ] Memory usage remains stable when processing 100+ images in sequence
- [ ] No memory leaks detected in profiling tools
- [ ] Existing image processing functionality remains intact
- [ ] Processing time does not significantly increase

## Implementation Notes
- The issue is likely in `src/services/ImageProcessor.js` around line 45-60
- Similar issue was fixed in the PDF processor by properly disposing of buffers
- Consider using weak references for cached thumbnails
- The `sharp` library instances need to be explicitly destroyed

## Related Context
- Related to issue #123 (PDF processing memory leak fix)
- Memory profiling results attached in previous comments
- Production logs show crashes during high-volume periods

## Testing Notes
- Run the memory profiling script: `npm run test:memory`
- Process the test image set in `test/fixtures/large-images/`
- Monitor memory usage with `htop` during processing
```

### Example 3: Documentation Update
```markdown
## Summary
Update the API documentation to include the new user preference endpoints added in PR #456.

## Current Behavior
API docs are missing the recently added preference endpoints, making it hard for frontend developers to integrate.

## Expected Behavior
Complete documentation for all preference endpoints with examples and response schemas.

## Acceptance Criteria
- [ ] Document GET /api/users/{id}/preferences endpoint
- [ ] Document PUT /api/users/{id}/preferences endpoint
- [ ] Include request/response examples for both endpoints
- [ ] Add error response documentation (400, 401, 404)
- [ ] Update the API changelog with new endpoints

## Implementation Notes
- Follow the existing documentation format in `docs/api/users.md`
- Use the same OpenAPI schema patterns as other endpoints
- The endpoint implementation is in `src/routes/userPreferences.js` for reference
- Include the JSON schema from `src/schemas/userPreferences.json`

## Related Context
- Implements feature request from issue #234
- Frontend team is waiting for docs to start integration
- PR #456 added the actual endpoints

## Testing Notes
- Verify all examples work with the actual API
- Check that schema validation matches implementation
- Test with API testing tool (Postman/Insomnia)
```

## Labels to Use

When creating issues for the auto runner, make sure to add these labels:
- `auto` (required - tells the runner this issue is eligible)
- `claude-help-wanted` (required - confirms you want Claude to work on it)
- Additional descriptive labels like:
  - `bug` (for bug fixes)
  - `enhancement` (for new features)  
  - `documentation` (for doc updates)
  - `ui` (for user interface changes)
  - `api` (for backend/API work)

## Tips for Success

### ✅ Do:
- Break large tasks into smaller, focused issues
- Include specific file paths and line numbers when relevant
- Provide examples of similar existing code
- Be explicit about testing requirements
- Reference related issues and PRs
- Include error messages or logs when reporting bugs

### ❌ Don't:
- Create issues that require multiple PRs to complete
- Ask for architectural decisions or design choices
- Include tasks that require external dependencies or setup
- Request changes that affect multiple unrelated systems
- Leave acceptance criteria vague or untestable

### Size Guidelines:
- **Good size**: Can be implemented in 1-3 files with < 100 lines of changes
- **Too small**: Typo fixes, single-line changes (do these manually)
- **Too large**: Features requiring new database tables, major refactors, or multiple services

Remember: The goal is to give Claude enough context to implement the task correctly on the first try, following your project's existing patterns and conventions.