import os
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

import os
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

import os
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .validators import validate_image_extension, validate_image_size

@login_required
def update_profile_image(request):
    """Handle the profile image update"""
    if request.method == 'POST' and request.FILES.get('profile_image'):
        member = request.user.member
        uploaded_file = request.FILES['profile_image']

        try:
            # Validate the file before saving
            validate_image_extension(uploaded_file)
            validate_image_size(uploaded_file)

            # Delete old image file if it exists
            if member.profile_image:
                if os.path.isfile(member.profile_image.path):
                    os.remove(member.profile_image.path)

            # Save new image
            member.profile_image = uploaded_file
            member.save()

            messages.success(request, 'Profile picture updated successfully!')

        except ValidationError as e:
            messages.error(request, str(e))

    else:
        messages.error(request, 'Please select a valid image file.')

    return redirect('members:member_profile')


@login_required
def remove_profile_image(request):
    """Remove the profile image"""
    member = request.user.member

    if member.profile_image:
        # Delete the image file
        if os.path.isfile(member.profile_image.path):
            os.remove(member.profile_image.path)

        # Clear the field
        member.profile_image = None
        member.save()

        messages.success(request, 'Profile picture removed successfully!')

    return redirect('members:member_profile')
