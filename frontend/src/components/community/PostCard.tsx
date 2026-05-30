import { Flame, Heart, MessageCircle, Sparkles } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'

export interface CommunityPost {
  id: string
  userName: string
  initials: string
  timestamp: string
  title: string
  content: string
  likes: number
  replies: number
  featured?: 'trending' | 'most-liked'
}

export function PostCard({ post }: { post: CommunityPost }) {
  return (
    <Card
      variant="gradient"
      className="overflow-hidden border-white/10 bg-white/[0.03] p-5 shadow-[0_20px_80px_-44px_rgba(178,0,67,0.55)]"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl border border-white/10 bg-gradient-to-br from-primary/30 via-primary/15 to-accent/20 text-sm font-semibold text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]">
            {post.initials}
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold text-white">{post.userName}</p>
              <span className="text-xs text-white/30">•</span>
              <p className="text-xs text-white/45">{post.timestamp}</p>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {post.featured === 'trending' && (
                <Badge variant="accent" className="gap-1.5">
                  <Flame className="h-3.5 w-3.5" />
                  Trending discussion
                </Badge>
              )}
              {post.featured === 'most-liked' && (
                <Badge variant="matched" className="gap-1.5">
                  <Sparkles className="h-3.5 w-3.5" />
                  Most liked question
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        <h3 className="text-lg font-semibold tracking-tight text-white">{post.title}</h3>
        <p className="text-sm leading-6 text-white/68">{post.content}</p>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3 text-sm text-white/55">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5">
          <Heart className="h-4 w-4 text-primary" />
          <span>{post.likes} likes</span>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5">
          <MessageCircle className="h-4 w-4 text-accent" />
          <span>{post.replies} replies</span>
        </div>
      </div>
    </Card>
  )
}