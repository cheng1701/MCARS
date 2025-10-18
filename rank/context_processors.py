from .models import RankSettings

def rank_defaults(request):
    """
    Add rank default settings to the template context
    """
    from .models import RankSettings

    settings = RankSettings.get_settings()

    return {
        'rank_settings': settings
    }
