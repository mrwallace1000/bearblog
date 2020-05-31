from django.shortcuts import get_object_or_404, redirect, render
from markdown import markdown
import tldextract
from django.http import Http404
from feedgen.feed import FeedGenerator

from .models import Blog, Post
from .helpers import unmark, get_base_root, get_root, is_protected
from blogs.helpers import get_nav, get_post, get_posts
from django.http import HttpResponse
from django.db.models import Count


def home(request):
    http_host = request.META['HTTP_HOST']

    if http_host == 'bearblog.dev' or http_host == 'localhost:8000':
        return render(request, 'landing.html')
    elif 'bearblog.dev' in http_host or 'localhost:8000' in http_host:
        extracted = tldextract.extract(http_host)
        if is_protected(extracted.subdomain):
            return redirect(get_base_root(extracted))

        blog = get_object_or_404(Blog, subdomain=extracted.subdomain)
        root = get_root(extracted, blog.subdomain)
    else:
        blog = get_object_or_404(Blog, domain=http_host)
        root = http_host

    all_posts = blog.post_set.filter(publish=True).order_by('-published_date')

    content = markdown(blog.content, extensions=['fenced_code'])

    return render(
        request,
        'home.html',
        {
            'blog': blog,
            'content': content,
            'posts': get_posts(all_posts),
            'nav': get_nav(all_posts),
            'root': root,
            'meta_description': unmark(blog.content)[:160]
        })


def posts(request):
    http_host = request.META['HTTP_HOST']

    if http_host == 'bearblog.dev' or http_host == 'localhost:8000':
        return redirect('/')
    elif 'bearblog.dev' in http_host or 'localhost:8000' in http_host:
        extracted = tldextract.extract(http_host)
        if is_protected(extracted.subdomain):
            return redirect(get_base_root(extracted))

        blog = get_object_or_404(Blog, subdomain=extracted.subdomain)
        root = get_root(extracted, blog.subdomain)
    else:
        blog = get_object_or_404(Blog, domain=http_host)
        root = http_host

    all_posts = blog.post_set.filter(publish=True).order_by('-published_date')

    return render(
        request,
        'posts.html',
        {
            'blog': blog,
            'posts': get_posts(all_posts),
            'nav': get_nav(all_posts),
            'root': root,
            'meta_description':  unmark(blog.content)[:160]
        }
    )


def post(request, slug):
    http_host = request.META['HTTP_HOST']

    if http_host == 'bearblog.dev' or http_host == 'localhost:8000':
        return redirect('/')
    elif 'bearblog.dev' in http_host or 'localhost:8000' in http_host:
        extracted = tldextract.extract(http_host)
        if is_protected(extracted.subdomain):
            return redirect(get_base_root(extracted))

        blog = get_object_or_404(Blog, subdomain=extracted.subdomain)
        root = get_root(extracted, blog.subdomain)
    else:
        blog = get_object_or_404(Blog, domain=http_host)
        root = http_host

    if request.GET.get('preview'):
        all_posts = blog.post_set.all().order_by('-published_date')
    else:
        all_posts = blog.post_set.filter(publish=True).order_by('-published_date')

    post = get_post(all_posts, slug)

    content = markdown(post.content, extensions=['fenced_code'])

    return render(
        request,
        'post.html',
        {
            'blog': blog,
            'content': content,
            'post': post,
            'nav': get_nav(all_posts),
            'root': root,
            'meta_description': unmark(post.content)[:160]
        }
    )


def feed(request):
    http_host = request.META['HTTP_HOST']

    if http_host == 'bearblog.dev' or http_host == 'localhost:8000':
        return redirect('/')
    elif 'bearblog.dev' in http_host or 'localhost:8000' in http_host:
        extracted = tldextract.extract(http_host)
        if is_protected(extracted.subdomain):
            return redirect(get_base_root(extracted))

        blog = get_object_or_404(Blog, subdomain=extracted.subdomain)
        root = get_root(extracted, blog.subdomain)
    else:
        blog = get_object_or_404(Blog, domain=http_host)
        root = http_host

    all_posts = blog.post_set.filter(publish=True, is_page=False).order_by('-published_date')

    fg = FeedGenerator()
    fg.id(f'{root}/')
    fg.author({'name': blog.subdomain, 'email': 'hidden'})
    fg.title(blog.title)
    fg.subtitle(unmark(blog.content)[:160])
    fg.link(href=f"{root}/feed/", rel='self')
    fg.link(href=root, rel='alternate')

    for post in all_posts:
        fe = fg.add_entry()
        fe.id(f"{root}/{post.slug}")
        fe.title(post.title)
        fe.author({'name': blog.subdomain, 'email': 'hidden'})
        fe.link(href=f"{root}/feed")
        fe.content(unmark(post.content))

    atomfeed = fg.atom_str(pretty=True)
    return HttpResponse(atomfeed, content_type='application/atom+xml')


def not_found(request, *args, **kwargs):
    return render(request, '404.html', status=404)


def board(request):
    http_host = request.META['HTTP_HOST']

    if not (http_host == 'bearblog.dev' or http_host == 'localhost:8000'):
        raise Http404("No Post matches the given query.")

    posts_per_page = 2
    page = 0
    if request.GET.get('page'):
        page = int(request.GET.get('page'))
    posts_from = page * posts_per_page
    posts_to = (page * posts_per_page) + posts_per_page
    posts = Post.objects.annotate(upvote_count=Count('upvote')).order_by(
        '-upvote_count', '-published_date').select_related('blog')[posts_from:posts_to]

    return render(request, 'board.html', {
        'posts': posts,
        'next_page': page+1,
        'posts_from': posts_from})
