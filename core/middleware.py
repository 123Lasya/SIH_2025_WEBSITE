import django.shortcuts
import django.template.loader as template_loader
from django.template import TemplateDoesNotExist


class LanguageTemplateMiddleware:
    """Per-request monkeypatch of `django.shortcuts.render`.

    This wrapper checks `request.session['lang']` and maps template names
    ending with `.html` to `_te.html` or `_hi.html` before calling the
    original `django.shortcuts.render`. It restores the original render
    after the request.

    Rationale: lets existing views keep calling `render(request, 'x.html', ...)`
    without modification.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        original_render = django.shortcuts.render
        original_get_template = template_loader.get_template

        def lang_render(req, template_name, context=None, *args, **kwargs):
            # prefer session, fallback to cookie, default to 'en'
            try:
                lang = getattr(req, "session", {}).get("lang") or req.COOKIES.get("lang") or "en"
            except Exception:
                lang = "en"

            if isinstance(template_name, str) and template_name.endswith('.html'):
                if lang == 'te':
                    alt = template_name.replace('.html', '_te.html')
                    template_name = alt
                elif lang == 'hi':
                    alt = template_name.replace('.html', '_hi.html')
                    template_name = alt

            return original_render(req, template_name, context or {}, *args, **kwargs)

        def lang_get_template(name, *args, **kwargs):
            # Try language-specific template first, then fall back to original
            try:
                lang = getattr(request, "session", {}).get("lang") or request.COOKIES.get("lang") or "en"
            except Exception:
                lang = "en"

            if isinstance(name, str) and name.endswith('.html'):
                if lang == 'te':
                    alt = name.replace('.html', '_te.html')
                    try:
                        return original_get_template(alt, *args, **kwargs)
                    except TemplateDoesNotExist:
                        pass
                elif lang == 'hi':
                    alt = name.replace('.html', '_hi.html')
                    try:
                        return original_get_template(alt, *args, **kwargs)
                    except TemplateDoesNotExist:
                        pass

            return original_get_template(name, *args, **kwargs)

        # Monkeypatch render and template loader for the duration of this request
        django.shortcuts.render = lang_render
        template_loader.get_template = lang_get_template

        try:
            response = self.get_response(request)
        finally:
            # restore originals to avoid cross-request leakage
            django.shortcuts.render = original_render
            template_loader.get_template = original_get_template

        return response
