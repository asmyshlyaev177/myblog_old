from django.contrib.sitemaps import Sitemap
from blog.models import Post

class BlogSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5
    limit = 40000

    def items(self):
        return Post.objects.filter(status="P", private=False)

    def lastmod(self, obj):
        return obj.edited