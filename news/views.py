from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Prefetch, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone

from accounts.models import StudentProfile
from .models import News, Category, Comment
from .forms import CommentForm
from django.views.decorators.cache import cache_page
from functools import reduce
import operator

from django.utils.decorators import method_decorator
from django.core.cache import cache
from datetime import timedelta

class HomePageView(TemplateView):
    template_name = "home.html"
    
    @method_decorator(cache_page(60 * 15))  # Cache the page for 15 minutes
    def dispatch(self, *args, **kwargs):
        """Use Django's built-in cache for entire page"""
        return super().dispatch(*args, **kwargs)
    
    def get_latest_news(self):
        """Get latest articles with optimized queries"""
        cache_key = 'latest_news'
        latest_news = cache.get(cache_key)
        
        if not latest_news:
            # Using select_related to fetch related models in a single query
            latest_news = News.objects.select_related(
                'category', 'author', 'author__user'
            ).filter(
                status='published', 
                publish_date__lte=timezone.now()
            ).only(
                'id', 'title', 'slug', 'summary', 'featured_image', 
                'publish_date', 'views', 
                'author', 'author__user', 'category',
                'category__name', 
                'category__slug'
            ).order_by('-publish_date')[:10]
            
            # Calculate comment count efficiently
            articles_with_comments = News.objects.filter(
                id__in=[article.id for article in latest_news]
            ).annotate(
                comment_count=Count('comments', filter=Q(comments__is_approved=True))
            ).values('id', 'comment_count')
            
            # Create a dictionary for fast lookup
            comment_counts = {item['id']: item['comment_count'] for item in articles_with_comments}
            
            # Add comment count to each article
            for article in latest_news:
                article.comment_count = comment_counts.get(article.id, 0)
            
            # Cache for 5 minutes
            cache.set(cache_key, latest_news, 60 * 5)
        
        return latest_news
    
    def get_featured_articles(self):
        """Get featured articles"""
        cache_key = 'featured_articles'
        featured_articles = cache.get(cache_key)
        
        if not featured_articles:
            featured_articles = News.objects.select_related(
                'category', 'author', 'author__user'
            ).filter(
                is_featured=True,
                status='published',
                publish_date__lte=timezone.now()
            ).only(
                'id', 'title', 'slug', 'summary', 'featured_image', 
                'publish_date',
                'author', 'author__user',
                'category', 'category__name', 'category__slug'
            ).order_by('-publish_date')[:3]
            
            cache.set(cache_key, featured_articles, 60 * 10)  # Cache for 10 minutes
        
        return featured_articles
    
    def get_category_articles(self):
        """Get articles organized by featured categories"""
        cache_key = 'category_articles'
        featured_categories = cache.get(cache_key)
        
        if not featured_categories:
            # Get categories that have articles
            categories = Category.objects.filter(
                news__status='published',  
                news__publish_date__lte=timezone.now()
            ).distinct().only('id', 'name', 'slug')[:6]
            
            featured_categories = []
            for category in categories:
                # For each category, get the latest 3 articles
                articles = News.objects.filter(
                    category=category,
                    status='published',
                    publish_date__lte=timezone.now()
                ).only(
                    'id', 'title', 'slug', 'featured_image', 'publish_date'
                ).order_by('-publish_date')[:3]
                
                category.articles = list(articles)
                featured_categories.append(category)
            
            cache.set(cache_key, featured_categories, 60 * 15)  # Cache for 15 minutes
        
        return featured_categories
    
    def get_most_viewed(self):
        """Get most viewed articles in the last 30 days"""
        cache_key = 'most_viewed'
        most_viewed = cache.get(cache_key)
        
        if not most_viewed:
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            most_viewed = News.objects.select_related(
                'category'
            ).filter(
                status='published',
                publish_date__lte=timezone.now(),
                publish_date__gte=thirty_days_ago
            ).only(
                'id', 'title', 'slug', 'featured_image', 'publish_date', 'views', 'category'
            ).order_by('-views')[:5]
            
            cache.set(cache_key, most_viewed, 60 * 60)  # Cache for 1 hour
        
        return most_viewed
    
    def get_recent_comments(self):
        """Get recent comments with related user and article information"""
        cache_key = 'recent_comments'
        recent_comments = cache.get(cache_key)
        
        if not recent_comments:
            # Using select_related for optimization
            recent_comments = Comment.objects.select_related(
                'user', 'user__profile', 'news'
            ).filter(
                is_approved=True
            ).only(
                'id', 'content', 'created_at', 
                'user__first_name', 'user__last_name',
                'user__profile', 'news__slug'
            ).order_by('-created_at')[:5]
        
            # Add the timesince annotation to each comment object
            for comment in recent_comments:
                # Make sure the comment.created_at is timezone-aware
                comment.created_at = timezone.localtime(comment.created_at)  # Convert to the local timezone
            
            cache.set(cache_key, recent_comments, 60 * 5)  # Cache for 5 minutes
        
        return recent_comments
    
    def get_writers(self):
        """Get active student profiles for writers"""
        cache_key = 'active_writers'
        writers = cache.get(cache_key)
        
        if not writers:
            # Get active writers who have published at least one article
            writers = StudentProfile.objects.select_related(
                'user', 'user__profile' 
            ).filter(
                user__is_active=True,
                news_posts__isnull=False,  # Has at least one news post
                news_posts__status='published'  # Has at least one published post
            ).distinct().only(
                'id', 'slug', 'profile_picture', 'bio',
                'user__first_name', 'user__last_name', 'user__profile' 
            )[:8]
            
            cache.set(cache_key, writers, 60 * 60)  # Cache for 1 hour
        
        return writers
    
    def get_categories(self):
        """Get all categories with published articles"""
        cache_key = 'all_categories'
        categories = cache.get(cache_key)
        
        if not categories:
            # Only get categories that have published articles
            categories = Category.objects.filter(
                news__status='published'
            ).distinct().order_by('name')
            
            cache.set(cache_key, categories, 60 * 60 * 12)  # Cache for 12 hours
        
        return categories
    
    def get_popular_news(self):
        """Get popular news for sidebar/footer"""
        cache_key = 'popular_news'
        popular_news = cache.get(cache_key)
        
        if not popular_news:
            # Get articles with most comments in the last 7 days
            seven_days_ago = timezone.now() - timedelta(days=7)
            
            popular_news = News.objects.select_related(
                'category'
            ).filter(
                status='published',
                publish_date__lte=timezone.now(),
                publish_date__gte=seven_days_ago
            ).annotate(
                comment_count=Count('comments', filter=Q(comments__is_approved=True))
            ).order_by('-comment_count', '-views')[:5]
            
            cache.set(cache_key, popular_news, 60 * 30)  # Cache for 30 minutes
        
        return popular_news
    
    def get_trending_tags(self):
        """Get trending tags from recent articles"""
        cache_key = 'trending_tags'
        trending_tags = cache.get(cache_key)
        
        if not trending_tags:
            # Get commonly used tags from articles in the last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            # Get IDs of recent published articles
            recent_article_ids = News.objects.filter(
                status='published',
                publish_date__lte=timezone.now(),
                publish_date__gte=thirty_days_ago
            ).values_list('id', flat=True)
            
            # Use the taggit manager to find most common tags
            from taggit.models import Tag
            trending_tags = Tag.objects.filter(
                news__id__in=recent_article_ids
            ).annotate(
                num_times=Count('news')
            ).order_by('-num_times')[:10]
            
            cache.set(cache_key, trending_tags, 60 * 60)  # Cache for 1 hour
        
        return trending_tags
    
    def get_context_data(self, **kwargs):
        """Prepare and combine all context data"""
        context = super().get_context_data(**kwargs)
        
        # Get latest news first as we'll use it in multiple places
        latest_news = self.get_latest_news()
        
        # Get featured articles
        featured_articles = self.get_featured_articles()
        
        # Prepare context with all required data
        context.update({
            'latest_news': latest_news,
            'featured_article': featured_articles[0] if featured_articles else None,
            'secondary_featured': featured_articles[1:3] if len(featured_articles) > 1 else [],
            'categories': self.get_categories(),
            'featured_categories': self.get_category_articles(),
            'writers': self.get_writers(),
            'most_viewed': self.get_most_viewed(),
            'recent_comments': self.get_recent_comments(),
            'popular_news': self.get_popular_news(),
            'trending_tags': self.get_trending_tags(),
        })
        
        return context

# @cache_page(60 * 60)
class NewsList(ListView):
    model = News
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 8
    
    def get_queryset(self):
        return News.objects.filter(status='published').order_by('-publish_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['featured_news'] = News.objects.filter(is_featured=True, status='published').order_by('-publish_date')[:5]
        context['popular_news'] = News.objects.filter(status='published').order_by('-views')[:5]
        context['recent_news'] = News.objects.filter(status='published').order_by('-publish_date')[:5]
        return context

# @cache_page(60 * 60)
class CategoryNews(ListView):
    model = News
    template_name = 'news/category_news.html'
    context_object_name = 'news_list'
    paginate_by = 8
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return News.objects.filter(category=self.category, status='published').order_by('-publish_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.all()
        return context

class NewsDetail(DetailView):
    model = News
    template_name = 'news/news_detail.html'
    context_object_name = 'news'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        news = self.get_object()
        
        # Increase view count
        news.increase_views()
        
        # Related news based on same category
        related_news = News.objects.filter(category=news.category, status='published').exclude(id=news.id).order_by('-publish_date')[:3]
        context['related_news'] = related_news
        
        # Comments
        comments = news.approved_comments()
        context['comments'] = comments
        context['comment_form'] = CommentForm()
        
        # Categories for sidebar
        context['categories'] = Category.objects.all()
        
        # Popular news for sidebar
        context['popular_news'] = News.objects.filter(status='published').order_by('-views')[:5]
        
        # Media files
        context['media_files'] = news.media_files.all().order_by('order')
        
        # Organize media files by type for easy access in templates
        context['images'] = news.media_files.filter(media_type='image').order_by('order')
        context['videos'] = news.media_files.filter(media_type='video').order_by('order')
        context['documents'] = news.media_files.filter(media_type='document').order_by('order')
        context['audio_files'] = news.media_files.filter(media_type='audio').order_by('order')
        
        # Get featured media if any
        context['featured_media'] = news.media_files.filter(is_featured=True).first()
        
        return context
    
    
@login_required
def add_comment(request, slug):
    news = get_object_or_404(News, slug=slug)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.news = news
            comment.user = request.user
            comment.save()
            return redirect('news:news_detail', slug=news.slug)
    
    return redirect('news:news_detail', slug=news.slug)

@cache_page(60 * 15)  # Cache the results for 15 minutes
def search_news(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    sort_by = request.GET.get('sort', '-publish_date')  # Default sort by newest
    results = []
    
    if query:
        # Split the query into keywords for better search
        keywords = query.split()
        
        # Create a base queryset with published news only
        base_queryset = News.objects.filter(status='published')
        
        # Apply category filter if provided
        if category_id:
            try:
                base_queryset = base_queryset.filter(category_id=int(category_id))
            except (ValueError, TypeError):
                pass  # Ignore invalid category_id
        
        # Search in multiple fields with OR condition
        search_fields = ['title', 'content', 'summary', 'tags__name', 'author__user__first_name', 'author__user__last_name']
        
        # Handle complex queries with multiple keywords
        if len(keywords) > 1:
            # For each keyword, create a complex query across all fields
            keyword_queries = []
            for keyword in keywords:
                field_queries = [Q(**{f"{field}__icontains": keyword}) for field in search_fields]
                keyword_queries.append(reduce(operator.or_, field_queries))
            
            # Combine all keyword queries with AND logic
            results = base_queryset.filter(reduce(operator.and_, keyword_queries))
        else:
            # Simple query with a single keyword
            field_queries = [Q(**{f"{field}__icontains": query}) for field in search_fields]
            results = base_queryset.filter(reduce(operator.or_, field_queries))
        
        # Apply sorting
        results = results.distinct().order_by(sort_by)
    else:
        # If no query provided, show featured or recent news
        results = News.objects.filter(status='published')
        if category_id:
            try:
                results = results.filter(category_id=int(category_id))
            except (ValueError, TypeError):
                pass
        results = results.order_by(sort_by)
    
    # Pagination
    per_page = int(request.GET.get('per_page', 8))  # Allow customizing items per page
    paginator = Paginator(results, per_page)
    page = request.GET.get('page')
    
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    
    # Get popular searches or categories for sidebar
    popular_tags = News.objects.filter(status='published').values(
        'tags__name'
    ).exclude(tags__name=None).order_by('tags__name').distinct()[:10]
    
    context = {
        'results': paginated_results,
        'query': query,
        'categories': Category.objects.all(),
        'popular_tags': popular_tags,
        'current_category': category_id,
        'current_sort': sort_by,
        'total_results': paginator.count,
    }
    
    return render(request, 'news/search_results.html', context)