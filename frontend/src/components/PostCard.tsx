import type { Post } from '../lib/api'

export default function PostCard({ post }: { post: Post }) {
  return (
    <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <img src={post.image_url} alt="" className="aspect-square w-full object-cover" loading="lazy" />
      <div className="p-3">
        {post.caption && <p className="text-sm text-slate-700">{post.caption}</p>}
        <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
          <span className="font-medium text-slate-600">{post.poster_pseudonym}</span>
          <time dateTime={post.created_at}>{new Date(post.created_at).toLocaleString()}</time>
        </div>
      </div>
    </article>
  )
}
