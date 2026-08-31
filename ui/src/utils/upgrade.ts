import { t } from '@/locales'
import { MsgWarning } from '@/utils/message'

const upgradeUrl = import.meta.env.VITE_UPGRADE_URL || ''

export function openUpgradeUrl() {
  if (upgradeUrl) {
    window.open(upgradeUrl, '_blank')
    return
  }

  MsgWarning(t('views.application.tip.professionalMessage'))
}
