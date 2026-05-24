import { useCallback, useEffect, useRef, useState } from 'react'
import PostCard from '../components/PostCard'
import UploadModal from '../components/UploadModal'
import { postsApi, type Post } from '../lib/api'

const PAGE_SIZE = 12

export default function FeedPage() {
  const [posts, setPosts] = useState<Post[]>([])
  const [skip, setSkip] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)
  const [uploadOpen, setUploadOpen] = useState(false)
  const sentinelRef = useRef<HTMLDivElement>(null)

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return
    setLoading(true)
    try {
      const { data } = await postsApi.feed(skip, PAGE_SIZE)
      setPosts((prev) => [...prev, ...data])
      setSkip((s) => s + data.length)
      if (data.length < PAGE_SIZE) setHasMore(false)
    } catch {
      setHasMore(false)
    } finally {
      setLoading(false)
    }
  }, [skip, loading, hasMore])

  useEffect(() => {
    loadMore()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const el = sentinelRef.current
    if (!el) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) loadMore()
      },
      { rootMargin: '200px' },
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [loadMore])

  function refreshFeed() {
    setPosts([])
    setSkip(0)
    setHasMore(true)
    setLoading(false)
    postsApi.feed(0, PAGE_SIZE).then(({ data }) => {
      setPosts(data)
      setSkip(data.length)
      setHasMore(data.length >= PAGE_SIZE)
    })
  }

  return (
    <div className="relative p-6">
      <h1 className="text-xl font-semibold text-slate-900">Feed</h1>
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {posts.map((post) => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>
      <div ref={sentinelRef} className="h-8" />
      {loading && <p className="py-4 text-center text-sm text-slate-500">Loading…</p>}
      {!hasMore && posts.length > 0 && (
        <p className="py-4 text-center text-sm text-slate-400">No more posts</p>
      )}

      <button
        type="button"
        onClick={() => setUploadOpen(true)}
        className="fixed bottom-8 right-8 flex h-14 w-14 items-center justify-center rounded-full bg-slate-900 text-2xl text-white shadow-lg hover:bg-slate-800"
        aria-label="Upload post"
      >
        +
      </button>

      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} onUploaded={refreshFeed} />
    </div>
  )
}
