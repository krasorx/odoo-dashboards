/** @odoo-module */

// Indexed by BOM level — last entry repeats for deeper levels
export const LEVEL_BADGES = [
    'bg-blue-100 text-blue-800',
    'bg-sky-100 text-sky-800',
    'bg-teal-100 text-teal-800',
    'bg-violet-100 text-violet-800',
    'bg-pink-100 text-pink-800',
];

export function levelBadge(level) {
    return LEVEL_BADGES[Math.min(level, LEVEL_BADGES.length - 1)];
}
