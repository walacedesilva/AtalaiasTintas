# Accessibility Checklist - Modern Web Interface (WCAG 2.1 AA)

## Perceivable

### Color & Contrast
- [ ] Text contrast ratio ≥ 4.5:1 against background (AA standard)
- [ ] Large text contrast ratio ≥ 3:1 against background
- [ ] Color is not the only means of conveying information
- [ ] Focus indicators have sufficient contrast (≥ 3:1)
- [ ] UI component contrast meets AA standards

### Images & Media
- [ ] All images have appropriate alt text
- [ ] Decorative images use empty alt="" or CSS background
- [ ] Complex images have detailed descriptions
- [ ] Icons have accessible names or labels
- [ ] No information conveyed by image alone

### Text & Typography
- [ ] Text can be resized up to 200% without horizontal scrolling
- [ ] Font hierarchy clear with proper heading structure (h1-h6)
- [ ] Font size minimum 14px for body text
- [ ] Line height at least 1.5x font size
- [ ] Paragraph spacing at least 2x font size

## Operable

### Keyboard Navigation
- [ ] All interactive elements keyboard accessible
- [ ] Logical tab order throughout interface
- [ ] No keyboard traps (users can exit all elements)
- [ ] Skip links provided to main content areas
- [ ] Custom keyboard shortcuts don't conflict with AT

### Focus Management
- [ ] Focus indicators visible and distinctive
- [ ] Focus moves logically through interface
- [ ] Modal dialogs trap focus appropriately
- [ ] Focus returns to triggering element after modal close
- [ ] Focus not lost during page updates

### Timing & Motion
- [ ] No time limits for completing tasks (or user can extend)
- [ ] Auto-playing content can be paused/stopped
- [ ] Animation can be disabled (respects prefers-reduced-motion)
- [ ] No seizure-inducing content (< 3 flashes per second)
- [ ] Motion-based interactions have alternatives

### Touch Targets
- [ ] Touch targets minimum 44px × 44px
- [ ] Adequate spacing between touch targets
- [ ] Touch gestures have keyboard alternatives
- [ ] Drag and drop operations have alternatives

## Understandable

### Language & Readability
- [ ] Page language properly declared (lang attribute)
- [ ] Language changes marked up in content
- [ ] Content written at appropriate reading level
- [ ] Technical terms explained or linked to glossary
- [ ] Abbreviations explained on first use

### Navigation & Structure
- [ ] Consistent navigation across pages
- [ ] Breadcrumb navigation implemented
- [ ] Page titles descriptive and unique
- [ ] Heading structure logical and hierarchical
- [ ] Site search functionality accessible

### Forms & Input
- [ ] Form labels properly associated with inputs
- [ ] Required fields clearly marked
- [ ] Input format requirements explained
- [ ] Error messages clear and actionable
- [ ] Success confirmations provided

### Error Prevention
- [ ] Important submissions require confirmation
- [ ] Forms preserve data on validation errors
- [ ] Destructive actions require explicit confirmation
- [ ] Input validation happens before submission
- [ ] Clear recovery options for errors

## Robust

### Assistive Technology
- [ ] Screen reader compatible (tested with NVDA/JAWS)
- [ ] ARIA labels used appropriately
- [ ] ARIA roles assigned correctly
- [ ] ARIA states and properties updated dynamically
- [ ] Semantic HTML elements used properly

### Progressive Enhancement
- [ ] Core functionality works without JavaScript
- [ ] Graceful degradation for older browsers
- [ ] Content accessible without CSS
- [ ] No reliance on specific AT or browser
- [ ] Standards-compliant markup validated

## Testing Requirements

### Automated Testing
- [ ] axe-core accessibility testing integrated
- [ ] WAVE evaluation completed
- [ ] Lighthouse accessibility audit passed (score ≥ 90)
- [ ] HTML validation completed without errors
- [ ] Color contrast automated testing passed

### Manual Testing
- [ ] Keyboard-only navigation tested completely
- [ ] Screen reader testing completed (minimum NVDA)
- [ ] High contrast mode compatibility verified
- [ ] Zoom testing up to 200% completed
- [ ] Mobile accessibility testing completed

### User Testing
- [ ] Testing with users who use assistive technology
- [ ] Feedback incorporated from accessibility review
- [ ] Usability testing includes accessibility scenarios
- [ ] Documentation updated based on user feedback

## Specific UI Components

### Forms
- [ ] Label/input association verified
- [ ] Fieldset/legend used for related controls
- [ ] Error messages linked to fields (aria-describedby)
- [ ] Required field indication accessible
- [ ] Form submission feedback accessible

### Navigation
- [ ] Main navigation marked with nav role
- [ ] Breadcrumbs marked with nav role and aria-label
- [ ] Skip navigation links implemented
- [ ] Current page indicated in navigation
- [ ] Dropdown menus keyboard accessible

### Data Tables
- [ ] Table headers associated with data cells
- [ ] Complex tables use appropriate markup
- [ ] Table caption describes table purpose
- [ ] Sorting controls accessible
- [ ] Table responsive design maintains accessibility

### Dynamic Content
- [ ] ARIA live regions for status updates
- [ ] Loading states announced to screen readers
- [ ] Dynamic content changes announced
- [ ] Focus management during content updates
- [ ] Progress indicators accessible