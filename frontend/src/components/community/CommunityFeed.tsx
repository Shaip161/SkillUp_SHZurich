'use client'

import { useEffect, useId, useMemo, useState } from 'react'
import { Flame, MessageSquarePlus, Users, X } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { GlassCard } from '@/components/ui/Card'
import { PostCard, type CommunityPost } from './PostCard'

function initialsFor(name: string) {
    return name
        .split(' ')
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase() ?? '')
        .join('')
}

function buildMockPosts(skillName: string, subskillName: string): CommunityPost[] {
    const posts = [
        {
            id: `${subskillName}-practice`,
            userName: 'Nadia Chen',
            timestamp: '12 min ago',
            title: `Best way to practice ${subskillName} without sounding too textbook?`,
            content: `I can explain the concept, but my examples still feel generic. Has anyone found a 30-minute drill that actually maps back to the ${skillName} roadmap?`,
            likes: 31,
            replies: 12,
            featured: 'most-liked' as const,
        },
        {
            id: `${subskillName}-portfolio`,
            userName: 'Elias Romero',
            timestamp: '48 min ago',
            title: 'What would strong portfolio proof for this milestone look like?',
            content: `I want to turn ${subskillName} into something I can show in interviews. Would you ship a teardown, a small case study, or a workflow demo?`,
            likes: 18,
            replies: 15,
            featured: 'trending' as const,
        },
        {
            id: `${subskillName}-resources`,
            userName: 'Priya Solberg',
            timestamp: '2 h ago',
            title: `Resources that helped ${subskillName} finally click`,
            content: `Dropping a short list here: one practical walkthrough, one strong rubric example, and one framework I used to structure my answer before evaluation.`,
            likes: 14,
            replies: 7,
        },
        {
            id: `${subskillName}-feedback`,
            userName: 'Mateo Rivera',
            timestamp: 'Yesterday',
            title: 'Would anyone review my draft answer before I submit?',
            content: `I have a first pass ready for the practical stage and I am not sure whether it is concrete enough. Happy to swap feedback with anyone else moving through this path.`,
            likes: 9,
            replies: 6,
        },
    ]

    return posts.map((post) => ({
        ...post,
        initials: initialsFor(post.userName),
    }))
}

export function CommunityFeed({
    skillName,
    subskillName,
}: {
    skillName: string
    subskillName: string
}) {
    const dialogTitleId = useId()
    const dialogDescriptionId = useId()
    const [posts, setPosts] = useState<CommunityPost[]>(() => buildMockPosts(skillName, subskillName))
    const [composerOpen, setComposerOpen] = useState(false)
    const [draftTitle, setDraftTitle] = useState('')
    const [draftQuestion, setDraftQuestion] = useState('')

    useEffect(() => {
        setPosts(buildMockPosts(skillName, subskillName))
        setComposerOpen(false)
        setDraftTitle('')
        setDraftQuestion('')
    }, [skillName, subskillName])

    useEffect(() => {
        if (!composerOpen) return

        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') setComposerOpen(false)
        }

        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [composerOpen])

    const activeMembers = useMemo(
        () => 18 + ((skillName.length * 3 + subskillName.length) % 19),
        [skillName.length, subskillName.length],
    )
    const mostLiked = useMemo(
        () => posts.reduce((top, post) => (post.likes > top.likes ? post : top), posts[0]),
        [posts],
    )
    const trending = useMemo(
        () => posts.reduce((top, post) => (post.replies > top.replies ? post : top), posts[0]),
        [posts],
    )

    const submitDraft = () => {
        const title = draftTitle.trim()
        const content = draftQuestion.trim()
        if (!title || !content) return

        setPosts((current) => [
            {
                id: `local-${Date.now()}`,
                userName: 'You',
                initials: 'YO',
                timestamp: 'Just now',
                title,
                content,
                likes: 0,
                replies: 0,
            },
            ...current,
        ])
        setDraftTitle('')
        setDraftQuestion('')
        setComposerOpen(false)
    }

    return (
        <section className="space-y-5">
            <GlassCard className="relative overflow-hidden rounded-3xl p-5 sm:p-6">
                <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,112,0,0.16),transparent_28%),radial-gradient(circle_at_top_left,rgba(178,0,67,0.2),transparent_36%)]" />
                <div className="relative flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                    <div className="space-y-3">
                        <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="neutral">Frontend mock activity</Badge>
                            <Badge variant="accent" className="gap-1.5">
                                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-accent">
                                    <span className="absolute inset-0 animate-ping rounded-full bg-accent/80" />
                                </span>
                                {activeMembers} learners online now
                            </Badge>
                        </div>
                        <div>
                            <h2 className="font-display text-2xl font-bold tracking-tight text-white">
                                Community feed
                            </h2>
                            <p className="mt-2 max-w-xl text-sm leading-6 text-white/68">
                                Ask blockers, compare workflows, and learn how other learners are approaching{' '}
                                {subskillName} inside the {skillName} path.
                            </p>
                        </div>
                    </div>

                    <Button className="shrink-0" onClick={() => setComposerOpen(true)}>
                        <MessageSquarePlus className="h-4 w-4" />
                        + Ask the community
                    </Button>
                </div>
            </GlassCard>

            <div className="grid gap-3 md:grid-cols-3">
                <GlassCard className="rounded-2xl p-4">
                    <div className="flex items-center gap-3">
                        <span className="grid h-10 w-10 place-items-center rounded-2xl bg-primary/15 text-primary ring-1 ring-primary/30">
                            <Users className="h-4 w-4" />
                        </span>
                        <div>
                            <p className="text-xs uppercase tracking-[0.18em] text-white/35">Active now</p>
                            <p className="mt-1 text-lg font-semibold text-white">{activeMembers} online</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="rounded-2xl p-4">
                    <div className="flex items-start gap-3">
                        <span className="mt-0.5 grid h-10 w-10 place-items-center rounded-2xl bg-accent/15 text-accent ring-1 ring-accent/30">
                            <Flame className="h-4 w-4" />
                        </span>
                        <div>
                            <p className="text-xs uppercase tracking-[0.18em] text-white/35">Trending discussion</p>
                            <p className="mt-1 line-clamp-2 text-sm font-medium leading-6 text-white/78">
                                {trending.title}
                            </p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="rounded-2xl p-4">
                    <div className="space-y-1.5">
                        <p className="text-xs uppercase tracking-[0.18em] text-white/35">Most liked question</p>
                        <p className="line-clamp-2 text-sm font-medium leading-6 text-white/78">
                            {mostLiked.title}
                        </p>
                        <p className="text-xs text-white/45">{mostLiked.likes} likes this week</p>
                    </div>
                </GlassCard>
            </div>

            <div className="space-y-4">
                {posts.map((post) => (
                    <PostCard key={post.id} post={post} />
                ))}
            </div>

            {composerOpen && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-base-950/72 p-4 backdrop-blur-md"
                    onClick={() => setComposerOpen(false)}
                >
                    <GlassCard
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby={dialogTitleId}
                        aria-describedby={dialogDescriptionId}
                        className="w-full max-w-xl rounded-[28px] p-6 sm:p-7"
                        onClick={(event) => event.stopPropagation()}
                    >
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <p className="text-xs uppercase tracking-[0.2em] text-white/35">Ask the community</p>
                                <h3 id={dialogTitleId} className="mt-2 font-display text-2xl font-semibold text-white">
                                    Start a discussion
                                </h3>
                                <p id={dialogDescriptionId} className="mt-2 text-sm leading-6 text-white/62">
                                    This is a frontend-only MVP mockup. Submitting will add your post locally to the feed.
                                </p>
                            </div>
                            <button
                                type="button"
                                onClick={() => setComposerOpen(false)}
                                className="grid h-10 w-10 place-items-center rounded-2xl border border-white/10 bg-white/[0.03] text-white/65 transition hover:border-white/20 hover:text-white"
                                aria-label="Close ask the community dialog"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>

                        <div className="mt-6 space-y-4">
                            <div>
                                <label htmlFor="community-post-title" className="mb-2 block text-sm font-medium text-white/72">
                                    Title
                                </label>
                                <input
                                    id="community-post-title"
                                    type="text"
                                    value={draftTitle}
                                    onChange={(event) => setDraftTitle(event.target.value)}
                                    placeholder="What are you trying to figure out?"
                                    className="w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white placeholder:text-white/25 focus:border-primary/50 focus:outline-none"
                                />
                            </div>

                            <div>
                                <label
                                    htmlFor="community-post-question"
                                    className="mb-2 block text-sm font-medium text-white/72"
                                >
                                    Question
                                </label>
                                <textarea
                                    id="community-post-question"
                                    rows={5}
                                    value={draftQuestion}
                                    onChange={(event) => setDraftQuestion(event.target.value)}
                                    placeholder={`Share the blocker, context, or example you want feedback on for ${subskillName}...`}
                                    className="w-full resize-y rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white placeholder:text-white/25 focus:border-primary/50 focus:outline-none"
                                />
                            </div>
                        </div>

                        <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
                            <p className="text-xs text-white/38">Mock numbers only. No backend or realtime logic connected.</p>
                            <div className="flex gap-3">
                                <Button variant="ghost" onClick={() => setComposerOpen(false)}>
                                    Cancel
                                </Button>
                                <Button onClick={submitDraft} disabled={!draftTitle.trim() || !draftQuestion.trim()}>
                                    Submit question
                                </Button>
                            </div>
                        </div>
                    </GlassCard>
                </div>
            )}
        </section>
    )
}