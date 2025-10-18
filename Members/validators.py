import os
from django.core.exceptions import ValidationError

def validate_image_extension(value):
    """
    Validate that the uploaded file has an allowed image extension
    """
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    ext = os.path.splitext(value.name)[1].lower()

    if ext not in allowed_extensions:
        raise ValidationError(
            f'File extension "{ext}" is not allowed. '
            f'Allowed extensions are: {", ".join(allowed_extensions)}'
        )

def validate_image_size(value):
    """
    Validate that the uploaded image is not too large
    """
    # Limit to 5MB
    limit = 5 * 1024 * 1024  # 5MB
    if value.size > limit:
        raise ValidationError('Image size should not exceed 5MB.')
