from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .models import DataFile
from .utils import process_csv_file, process_excel_file, forecast_timeseries
import json


@login_required
def dashboard_view(request):
    # Get all files for the user (not just processed ones)
    all_files = DataFile.objects.filter(user=request.user)
    processed_files = all_files.filter(status='processed')

    # Calculate total records across all processed files
    total_records = sum(f.record_count for f in processed_files)

    context = {
        'total_files': all_files.count(),
        'processed_files': processed_files.count(),
        'total_records': total_records,
        'recent_files': all_files[:10]  # Show recent 10 files with all statuses
    }

    return render(request, 'properties/dashboard.html', context)


@login_required
def upload_view(request):
    if request.method == 'POST':
        file = request.FILES.get('file')

        if not file:
            messages.error(request, 'Please select a file')
            return render(request, 'properties/upload.html')

        if file.size > 5 * 1024 * 1024:
            messages.error(request, 'File size exceeds 5MB limit')
            return render(request, 'properties/upload.html')

        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in ['csv', 'xlsx', 'xls']:
            messages.error(request, 'Invalid file format. Please upload CSV or Excel file.')
            return render(request, 'properties/upload.html')

        data_file = DataFile.objects.create(
            user=request.user,
            name=file.name,
            file=file,
            file_size=file.size,
            status='uploaded'
        )

        messages.success(request, f'File "{file.name}" uploaded successfully! You can now process it.')
        return redirect('file_list')

    return render(request, 'properties/upload.html')


@login_required
def file_list_view(request):
    files = DataFile.objects.filter(user=request.user)

    # Paginate with 15 files per page
    page_number = request.GET.get('page', 1)
    paginator = Paginator(files, 15)
    page_obj = paginator.get_page(page_number)

    context = {
        'files': page_obj,
        'page_obj': page_obj
    }
    return render(request, 'properties/file_list.html', context)


@login_required
def process_file_view(request, file_id):
    data_file = get_object_or_404(DataFile, id=file_id, user=request.user)

    if data_file.status == 'processed':
        messages.info(request, 'This file has already been processed')
        return redirect('file_detail', file_id=file_id)

    data_file.status = 'processing'
    data_file.save()

    file_extension = data_file.name.split('.')[-1].lower()

    try:
        if file_extension == 'csv':
            count, error = process_csv_file(data_file.file, request.user, data_file)
        elif file_extension in ['xlsx', 'xls']:
            count, error = process_excel_file(data_file.file, request.user, data_file)

        if count:
            data_file.status = 'processed'
            data_file.record_count = count
            data_file.processed_at = timezone.now()
            if error:
                data_file.error_message = str(error)
            data_file.save()
            messages.success(request, f'Successfully processed {count} records!')
        else:
            data_file.status = 'error'
            data_file.error_message = str(error)
            data_file.save()
            messages.error(request, f'Failed to process file: {error}')
    except Exception as e:
        data_file.status = 'error'
        data_file.error_message = str(e)
        data_file.save()
        messages.error(request, f'Error processing file: {str(e)}')

    return redirect('file_detail', file_id=file_id)


@login_required
def file_detail_view(request, file_id):
    data_file = get_object_or_404(DataFile, id=file_id, user=request.user)

    # Paginate data with 10 records per page
    page_number = request.GET.get('page', 1)
    paginator = Paginator(data_file.data if data_file.data else [], 10)
    page_obj = paginator.get_page(page_number)

    # Calculate statistics
    stats = {}
    if data_file.data and data_file.columns:
        for column in data_file.columns:
            column_data = [row.get(column, '') for row in data_file.data]

            # Count null/empty values
            null_count = sum(1 for val in column_data if val == '' or val is None)

            # Try to get numeric statistics
            numeric_values = []
            for val in column_data:
                try:
                    if val != '' and val is not None:
                        numeric_values.append(float(val))
                except (ValueError, TypeError):
                    pass

            stats[column] = {
                'null_count': null_count,
                'null_percentage': (null_count / len(column_data) * 100) if len(column_data) > 0 else 0,
                'is_numeric': len(numeric_values) > 0,
            }

            if numeric_values:
                stats[column].update({
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'mean': sum(numeric_values) / len(numeric_values),
                })

    context = {
        'data_file': data_file,
        'columns': data_file.columns,
        'page_obj': page_obj,
        'stats': stats,
        'stats_json': json.dumps(stats)
    }

    return render(request, 'properties/file_detail.html', context)


@login_required
def visualize_file_view(request, file_id):
    data_file = get_object_or_404(DataFile, id=file_id, user=request.user)

    if data_file.status != 'processed':
        messages.warning(request, 'This file needs to be processed first')
        return redirect('file_detail', file_id=file_id)

    # Calculate statistics
    stats = {}
    if data_file.data and data_file.columns:
        for column in data_file.columns:
            column_data = [row.get(column, '') for row in data_file.data]

            # Count null/empty values
            null_count = sum(1 for val in column_data if val == '' or val is None)

            # Try to get numeric statistics
            numeric_values = []
            for val in column_data:
                try:
                    if val != '' and val is not None:
                        numeric_values.append(float(val))
                except (ValueError, TypeError):
                    pass

            stats[column] = {
                'null_count': null_count,
                'null_percentage': (null_count / len(column_data) * 100) if len(column_data) > 0 else 0,
                'is_numeric': len(numeric_values) > 0,
            }

            if numeric_values:
                stats[column].update({
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'mean': sum(numeric_values) / len(numeric_values),
                })

    context = {
        'data_file': data_file,
        'data_json': json.dumps(data_file.data) if data_file.data else '[]',
        'columns': data_file.columns,
        'columns_json': json.dumps(data_file.columns) if data_file.columns else '[]',
        'stats': stats,
        'stats_json': json.dumps(stats)
    }

    return render(request, 'properties/visualize.html', context)


@login_required
@require_http_methods(["POST"])
def delete_file_view(request, file_id):
    data_file = get_object_or_404(DataFile, id=file_id, user=request.user)

    file_name = data_file.name
    data_file.delete()
    messages.success(request, f'File "{file_name}" has been deleted successfully.')
    return redirect('dashboard')


@login_required
@require_http_methods(["POST"])
def forecast_data_view(request, file_id):
    data_file = get_object_or_404(DataFile, id=file_id, user=request.user)

    if data_file.status != 'processed':
        return JsonResponse({'error': 'File not processed yet'}, status=400)

    try:
        body = json.loads(request.body)
        x_column = body.get('x_column')
        y_column = body.get('y_column')
        periods = int(body.get('periods', 5))
        method = body.get('method', 'linear')

        if not x_column or not y_column:
            return JsonResponse({'error': 'Missing x_column or y_column'}, status=400)

        if periods < 1 or periods > 20:
            return JsonResponse({'error': 'Periods must be between 1 and 20'}, status=400)

        result = forecast_timeseries(data_file.data, x_column, y_column, periods, method)

        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=400)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_column_view(request, file_id):
    data_file = get_object_or_404(DataFile, id=file_id, user=request.user)

    if data_file.status != 'processed':
        return JsonResponse({'error': 'File not processed yet'}, status=400)

    try:
        body = json.loads(request.body)
        column_name = body.get('column_name')

        if not column_name:
            return JsonResponse({'error': 'Missing column_name'}, status=400)

        if not data_file.columns or column_name not in data_file.columns:
            return JsonResponse({'error': 'Column not found'}, status=404)

        if len(data_file.columns) <= 1:
            return JsonResponse({'error': 'Cannot remove the last column'}, status=400)

        # Remove column from columns list
        data_file.columns.remove(column_name)

        # Remove column from all data records
        for record in data_file.data:
            if column_name in record:
                del record[column_name]

        data_file.save()

        return JsonResponse({
            'success': True,
            'message': f'Column "{column_name}" removed successfully',
            'remaining_columns': len(data_file.columns)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_null_records_view(request, file_id):
    data_file = get_object_or_404(DataFile, id=file_id, user=request.user)

    if data_file.status != 'processed':
        return JsonResponse({'error': 'File not processed yet'}, status=400)

    try:
        body = json.loads(request.body)
        column_name = body.get('column_name')
        remove_all = body.get('remove_all', False)

        if not remove_all and not column_name:
            return JsonResponse({'error': 'Missing column_name or remove_all flag'}, status=400)

        if column_name and (not data_file.columns or column_name not in data_file.columns):
            return JsonResponse({'error': 'Column not found'}, status=404)

        original_count = len(data_file.data)

        if remove_all:
            # Remove records that have ANY null/empty value
            data_file.data = [
                record for record in data_file.data
                if all(record.get(col) not in ['', None] for col in data_file.columns)
            ]
        else:
            # Remove records where the specific column has null/empty value
            data_file.data = [
                record for record in data_file.data
                if record.get(column_name) not in ['', None]
            ]

        new_count = len(data_file.data)
        removed_count = original_count - new_count

        if removed_count == 0:
            return JsonResponse({
                'success': True,
                'message': 'No null records found to remove',
                'removed_count': 0,
                'remaining_records': new_count
            })

        # Update record count
        data_file.record_count = new_count
        data_file.save()

        message = f'Removed {removed_count} record(s) with null values'
        if not remove_all and column_name:
            message = f'Removed {removed_count} record(s) with null values in column "{column_name}"'

        return JsonResponse({
            'success': True,
            'message': message,
            'removed_count': removed_count,
            'remaining_records': new_count
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
