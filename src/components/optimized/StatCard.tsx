'use client'

import { memo } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  label: string
  value: number
  icon: LucideIcon
  color?: string
}

export const StatCard = memo(function StatCard({ label, value, icon: Icon, color = 'primary' }: StatCardProps) {
  return (
    <Card className="bg-background-paper border-white/10 hover:border-primary/50 transition-colors">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-3xl font-bold mt-2">{value}</p>
          </div>
          <div className={`w-12 h-12 rounded-lg bg-${color}/20 flex items-center justify-center`}>
            <Icon className={`w-6 h-6 text-${color}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
})

