/**
 * Team Member Color Utilities
 *
 * Provides consistent color assignment for team member avatars across all pages.
 *
 * Algorithm: Sort members by ID, find index in sorted array, use modulo for color.
 * This ensures the same member always gets the same color regardless of page or data ordering.
 *
 * Handles ID gaps gracefully (e.g., if ID 8 is deleted, ID 9 still gets consistent color).
 *
 * Color repetition: For teams larger than 16 members, colors wrap around using modulo.
 * This is acceptable as the schedule rotation naturally spreads members across the calendar.
 */

// 16-color WCAG AA compliant palette
const TEAM_COLORS = [
    'team-color-1',  'team-color-2',  'team-color-3',  'team-color-4',
    'team-color-5',  'team-color-6',  'team-color-7',  'team-color-8',
    'team-color-9',  'team-color-10', 'team-color-11', 'team-color-12',
    'team-color-13', 'team-color-14', 'team-color-15', 'team-color-16'
];

/**
 * Get consistent color class for team member across all pages.
 *
 * @param {number} memberId - Team member ID from database
 * @param {Array} allMembers - Array of all team member objects (must have 'id' property)
 * @returns {string} Color class (e.g., 'team-color-5')
 *
 * @example
 * const members = [{id: 1, name: 'Alice'}, {id: 6, name: 'Carol'}];
 * getTeamColor(6, members); // Returns 'team-color-2' (Carol is 2nd in sorted array)
 */
function getTeamColor(memberId, allMembers) {
    // Sort by ID to ensure consistent ordering
    const sorted = [...allMembers].sort((a, b) => a.id - b.id);

    // Find position in sorted array
    const index = sorted.findIndex(m => m.id === memberId);

    // Handle not found (shouldn't happen, but defensive)
    if (index === -1) {
        console.warn(`Team member ID ${memberId} not found in members array`);
        return TEAM_COLORS[0]; // Default to first color
    }

    // Map to color palette using modulo (handles teams > 16 members)
    return TEAM_COLORS[index % TEAM_COLORS.length];
}
