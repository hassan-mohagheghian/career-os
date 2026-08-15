export const COLUMN_GRID_TEMPLATE = 'minmax(200px, 2fr) minmax(140px, 1.4fr) minmax(140px, 1.4fr) 160px 80px 120px 110px 90px 90px'

export const LEADING_COLUMN_WIDTH = '44px'

export function buildJobGridTemplate(showRowNumber: boolean, showPinned: boolean): string {
  const leading: string[] = []
  if (showRowNumber) leading.push(LEADING_COLUMN_WIDTH)
  if (showPinned) leading.push(LEADING_COLUMN_WIDTH)
  return leading.length ? `${leading.join(' ')} ${COLUMN_GRID_TEMPLATE}` : COLUMN_GRID_TEMPLATE
}
