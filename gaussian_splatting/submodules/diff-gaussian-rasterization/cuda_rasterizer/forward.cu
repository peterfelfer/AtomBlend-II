/*
 * Copyright (C) 2023, Inria
 * GRAPHDECO research group, https://team.inria.fr/graphdeco
 * All rights reserved.
 *
 * This software is free for non-commercial, research and evaluation use 
 * under the terms of the LICENSE.md file.
 *
 * For inquiries contact  george.drettakis@inria.fr
 */

#include "forward.h"
#include "auxiliary.h"
#include <math_functions.h>
#include <stdio.h>
#include <cooperative_groups.h>
#include <cooperative_groups/reduce.h>
#include <iostream>
#include <cuda_runtime.h>


namespace cg = cooperative_groups;

__device__ float3 operator*(const float3& a, const float& b) {
    return make_float3(a.x * b, a.y * b, a.z * b);
}
__device__ float3 operator*(const float& a, const float3& b) {
    return make_float3(a * b.x, a * b.y, a * b.z);
}
__device__ float3 operator*(const float3& a, const float3& b) {
    return make_float3(a.x * b.x, a.y * b.y, a.z * b.z);
}
__device__ float2 operator*(const float2& a, const float& b) {
    return make_float2(a.x * b, a.y * b);
}
__device__ float2 operator*(const float2& a, const int& b) {
    return make_float2(a.x * float(b), a.y * float(b));
}

__device__ float3 operator/(const float3& a, const float& b) {
    if (b == 0){
//        printf("CUDA ERROR at operator/ 3 1 ");
    }
    return make_float3(a.x / b, a.y / b, a.z / b);
}
__device__ float3 operator/(const float& a, const float3& b) {
    if (b.x == 0 || b.y == 0 || b.z == 0){
//        printf("CUDA ERROR at operator/ 1 3 ");
    }
    return make_float3(a / b.x, a / b.y, a / b.z);
}
__device__ float3 operator/(const float3& a, const float3& b) {
    if (b.x == 0 || b.y == 0 || b.z == 0){
//        printf("CUDA ERROR at operator/ 3 3 ");
    }
    return make_float3(a.x / b.x, a.y / b.y, a.z / b.z);
}
__device__ float2 operator/(const float2& a, const float& b) {
    if (b == 0){
//        printf("CUDA ERROR at operator/ 2 1 ");
    }
    return make_float2(a.x / b, a.y / b);
}

__device__ float3 operator-(const float3& a, const float3& b) {
    return make_float3(a.x - b.x, a.y - b.y, a.z - b.z);
}
__device__ float2 operator-(const float2& a, const float2& b) {
    return make_float2(a.x - b.x, a.y - b.y);
}
__device__ uint2 operator-(const uint2& a, const uint2& b) {
    return make_uint2(a.x - b.x, a.y - b.y);
}
__device__ float3 operator-(const float3& a, const float& b) {
    return make_float3(a.x - b, a.y - b, a.z - b);
}

__device__ float3 operator+(const float3& a, const float3& b) {
    return make_float3(a.x + b.x, a.y + b.y, a.z + b.z);
}
__device__ float3 operator+(const float3& a, const float& b) {
    return make_float3(a.x + b, a.y + b, a.z + b);
}

__device__ float3 normalize(const float3 &v) {
    float l = sqrtf(v.x * v.x + v.y * v.y + v.z * v.z);
    return make_float3(v.x / l, v.y / l, v.z / l);
}
__device__ float dot(const float3 &v1, const float3 &v2) {
    return v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
}
__device__ float length(const float3& a) {
    return sqrtf(dot(a,a));
}
__device__ float dot(const float2 &v1, const float2 &v2) {
    return v1.x * v2.x + v1.y * v2.y;
}
__device__ float length(const float2& a) {
    return sqrtf(dot(a,a));
}


// Forward method for converting the input spherical harmonics
// coefficients of each Gaussian to a simple RGB color.
__device__ glm::vec3 computeColorFromSH(int idx, int deg, int max_coeffs, const glm::vec3* means, glm::vec3 campos, const float* shs, bool* clamped)
{
	// The implementation is loosely based on code for 
	// "Differentiable Point-Based Radiance Fields for 
	// Efficient View Synthesis" by Zhang et al. (2022)
	glm::vec3 pos = means[idx];
	glm::vec3 dir = pos - campos;
	dir = dir / glm::length(dir);

	glm::vec3* sh = ((glm::vec3*)shs) + idx * max_coeffs;
	glm::vec3 result = SH_C0 * sh[0];

	if (deg > 0)
	{
		float x = dir.x;
		float y = dir.y;
		float z = dir.z;
		result = result - SH_C1 * y * sh[1] + SH_C1 * z * sh[2] - SH_C1 * x * sh[3];

		if (deg > 1)
		{
			float xx = x * x, yy = y * y, zz = z * z;
			float xy = x * y, yz = y * z, xz = x * z;
			result = result +
				SH_C2[0] * xy * sh[4] +
				SH_C2[1] * yz * sh[5] +
				SH_C2[2] * (2.0f * zz - xx - yy) * sh[6] +
				SH_C2[3] * xz * sh[7] +
				SH_C2[4] * (xx - yy) * sh[8];

			if (deg > 2)
			{
				result = result +
					SH_C3[0] * y * (3.0f * xx - yy) * sh[9] +
					SH_C3[1] * xy * z * sh[10] +
					SH_C3[2] * y * (4.0f * zz - xx - yy) * sh[11] +
					SH_C3[3] * z * (2.0f * zz - 3.0f * xx - 3.0f * yy) * sh[12] +
					SH_C3[4] * x * (4.0f * zz - xx - yy) * sh[13] +
					SH_C3[5] * z * (xx - yy) * sh[14] +
					SH_C3[6] * x * (xx - 3.0f * yy) * sh[15];
			}
		}
	}
	result += 0.5f;

	// RGB colors are clamped to positive values. If values are
	// clamped, we need to keep track of this for the backward pass.
	clamped[3 * idx + 0] = (result.x < 0);
	clamped[3 * idx + 1] = (result.y < 0);
	clamped[3 * idx + 2] = (result.z < 0);
	return glm::max(result, 0.0f);
}

// Forward version of 2D covariance matrix computation
__device__ float3 computeCov2D(const float3& mean, float focal_x, float focal_y, float tan_fovx, float tan_fovy, const float* cov3D, const float* viewmatrix, const float scale, const bool orthographic_cam)
{
	// The following models the steps outlined by equations 29
	// and 31 in "EWA Splatting" (Zwicker et al., 2002). 
	// Additionally considers aspect / scaling of viewport.
	// Transposes used to account for row-/column-major conventions.
	float3 t = transformPoint4x3(mean, viewmatrix);

	const float limx = 1.3f * tan_fovx;
	const float limy = 1.3f * tan_fovy;
	const float txtz = t.x / t.z;
	const float tytz = t.y / t.z;
	t.x = min(limx, max(-limx, txtz)) * t.z;
	t.y = min(limy, max(-limy, tytz)) * t.z;

    glm::mat3 J;
    if (!orthographic_cam){
    	J = glm::mat3(
		focal_x / t.z, 0.0f, -(focal_x * t.x) / (t.z * t.z),
		0.0f, focal_y / t.z, -(focal_y * t.y) / (t.z * t.z),
		0, 0, 0);
    } else {
    	J = glm::mat3(
		10, 0, 0,
		0, 10, 0,
		0, 0, 0);
    }

//    printf("focal %f, %f, \n", focal_x, focal_y);
//    printf("tan fov %f, %f, \n", tan_fovx, tan_fovy);

	glm::mat3 W = glm::mat3(
		viewmatrix[0], viewmatrix[4], viewmatrix[8],
		viewmatrix[1], viewmatrix[5], viewmatrix[9],
		viewmatrix[2], viewmatrix[6], viewmatrix[10]);

	glm::mat3 T = W * J;

	glm::mat3 Vrk = glm::mat3(
		cov3D[0] * scale, cov3D[1] * scale, cov3D[2] * scale,
		cov3D[1] * scale, cov3D[3] * scale, cov3D[4] * scale,
		cov3D[2] * scale, cov3D[4] * scale, cov3D[5] * scale);

	glm::mat3 cov = glm::transpose(T) * glm::transpose(Vrk) * T;

	// Apply low-pass filter: every Gaussian should be at least
	// one pixel wide/high. Discard 3rd row and column.
	cov[0][0] += 0.3f;
	cov[1][1] += 0.3f;
	return { float(cov[0][0]), float(cov[0][1]), float(cov[1][1]) };
}

// Forward method for converting scale and rotation properties of each
// Gaussian to a 3D covariance matrix in world space. Also takes care
// of quaternion normalization.
__device__ void computeCov3D(const glm::vec3 scale, float mod, const glm::vec4 rot, float* cov3D)
{
	// Create scaling matrix
	glm::mat3 S = glm::mat3(1.0f);
	S[0][0] = mod * scale.x;
	S[1][1] = mod * scale.y;
	S[2][2] = mod * scale.z;

	// Normalize quaternion to get valid rotation
	glm::vec4 q = glm::vec4(0.0f); //rot;// / glm::length(rot);
	float r = q.x;
	float x = q.y;
	float y = q.z;
	float z = q.w;

	// Compute rotation matrix from quaternion
	glm::mat3 R = glm::mat3(
		1.f - 2.f * (y * y + z * z), 2.f * (x * y - r * z), 2.f * (x * z + r * y),
		2.f * (x * y + r * z), 1.f - 2.f * (x * x + z * z), 2.f * (y * z - r * x),
		2.f * (x * z - r * y), 2.f * (y * z + r * x), 1.f - 2.f * (x * x + y * y)
	);

	glm::mat3 M = S; // * R;

	// Compute 3D world covariance matrix Sigma
	glm::mat3 Sigma = glm::transpose(M) * M;

	// Covariance is symmetric, only store upper right
	cov3D[0] = Sigma[0][0];
	cov3D[1] = Sigma[0][1];
	cov3D[2] = Sigma[0][2];
	cov3D[3] = Sigma[1][1];
	cov3D[4] = Sigma[1][2];
	cov3D[5] = Sigma[2][2];
}

// Perform initial steps for each Gaussian prior to rasterization.
template<int C>
__global__ void preprocessCUDA(int P, int D, int M,
	const float* orig_points,
	const glm::vec3* scales,
	const float scale_modifier,
	const glm::vec4* rotations,
	const float* opacities,
	bool* clamped,
	const float* cov3D_precomp,
	const float* viewmatrix,
	const float* projmatrix,
	const glm::vec3* cam_pos,
	const int W, int H,
	const float tan_fovx, float tan_fovy,
	const float focal_x, float focal_y,
	int* radii,
	int* radii_xy,
	float2* points_xy_image,
	float* depths,
	float* cov3Ds,
	float* rgb,
	float4* conic_opacity,
	const dim3 grid,
	uint32_t* tiles_touched,
	bool prefiltered,
	const float* indices,
	const float* index_properties,
	const bool orthographic_cam,
	const float individual_opacity_factor)
{
	auto idx = cg::this_grid().thread_rank();
	if (idx >= P)
		return;

	// Initialize radius and touched tiles to 0. If this isn't changed,
	// this Gaussian will not be processed further.
	radii[idx] = 0;
	tiles_touched[idx] = 0;

	// Perform near culling, quit if outside.
	float3 p_view;
	if (!in_frustum(idx, orig_points, viewmatrix, projmatrix, prefiltered, p_view))
		return;

	// Transform point by projecting
	float3 p_orig = { orig_points[3 * idx], orig_points[3 * idx + 1], orig_points[3 * idx + 2] };
	float4 p_hom = transformPoint4x4(p_orig, projmatrix);
	float p_w = 1.0f / (p_hom.w + 0.0000001f);
	float3 p_proj = { p_hom.x * p_w, p_hom.y * p_w, p_hom.z * p_w };

    // Get color and scale for corresponding index
	int index = indices[idx];
	float4 col = { index_properties[index * 5], index_properties[index * 5 + 1], index_properties[index * 5 + 2], index_properties[index * 5 + 3] };
    const float scale = index_properties[index * 5 + 4];

    if (col.w != 0.0){
        col.w = opacities[idx] + individual_opacity_factor;
        col.w = glm::clamp(col.w, 0.0f, 1.0f);
    }

    ////// DEBUG

//    float opacity = opacities[idx];
//    opacity = opacity / 1000;
//    opacity = 1 / opacity;
////    col = { 1, 1, 1, 1 };
//    col.x = opacity;
//    col.y = 0.0f;
//    col.z = 0.0f;
//
//    if (opacity < 0.5){
//        col.x = 0.0f;
//        col.y = 1.0f;
//        col.z = 0.0f;
//    }

//    if (opacity < 1){
//        col = { 1, 0, 0, 1 };
//    }
//    if (opacity < 0.8){
//        col = { 0, 1, 0, 1 };
//    }
//    if (opacity < 0.6){
//        col = { 0, 0, 1, 1 };
//    }
//    if (opacity < 0.4){
//        col = { 1, 1, 0, 1 };
//    }
//    if (opacity < 0.2){
//        col = { 0, 1, 1, 1 };
//    }


	// If 3D covariance matrix is precomputed, use it, otherwise compute
	// from scaling and rotation parameters. 
	const float* cov3D;
	if (cov3D_precomp != nullptr) // precomputed cov3D
	{
		cov3D = cov3D_precomp + idx * 6;
	}
	else // using identity matrix as cov3D
	{
//		computeCov3D(scales[idx], scale_modifier, rotations[idx], cov3Ds + idx * 6);
		int cov3D_idx = idx * 6;
        cov3Ds[cov3D_idx] = 1.0f;
        cov3Ds[cov3D_idx + 1] = 0.0f;
        cov3Ds[cov3D_idx + 2] = 0.0f;
        cov3Ds[cov3D_idx + 3] = 1.0f;
        cov3Ds[cov3D_idx + 4] = 0.0f;
        cov3Ds[cov3D_idx + 5] = 1.0f;
		cov3D = cov3Ds + idx * 6;
	}

	// Compute 2D screen-space covariance matrix
	float3 cov = computeCov2D(p_orig, focal_x, focal_y, tan_fovx, tan_fovy, cov3D, viewmatrix, scale, orthographic_cam);

	// Invert covariance (EWA algorithm)
	float det = (cov.x * cov.z - cov.y * cov.y);
	if (det == 0.0f)
		return;
	float det_inv = 1.f / det;
	float3 conic = { cov.z * det_inv, -cov.y * det_inv, cov.x * det_inv };

	// Compute extent in screen space (by finding eigenvalues of
	// 2D covariance matrix). Use extent to compute a bounding rectangle
	// of screen-space tiles that this Gaussian overlaps with. Quit if
	// rectangle covers 0 tiles. 
	float mid = 0.5f * (cov.x + cov.z);
	float lambda1 = mid + sqrt(max(0.1f, mid * mid - det));
	float lambda2 = mid - sqrt(max(0.1f, mid * mid - det));
	float my_radius = ceil(3.f * sqrt(max(lambda1, lambda2)));
	float my_radius_x = ceil(3.f * sqrt(lambda1));
	float my_radius_y = ceil(3.f * sqrt(lambda2));
	float2 point_image = { ndc2Pix(p_proj.x, W), ndc2Pix(p_proj.y, H) };
	uint2 rect_min, rect_max;
	getRect(point_image, my_radius, rect_min, rect_max, grid);

	if ((rect_max.x - rect_min.x) * (rect_max.y - rect_min.y) == 0)
		return;

    rgb[idx * C + 0] = col.x;
    rgb[idx * C + 1] = col.y;
    rgb[idx * C + 2] = col.z;

    // Calculate opacity
//    float volume = 4/3 * 3.14159 * cov3D[0] * cov3D[3] * cov3D[5];
//    float opacity = 1 / volume;
//
//    printf("%f, %f, %f, %f \n", cov3D[0], cov3D[3], cov3D[5], volume);
//    printf("%f \n", opacity);


	// Store some useful helper data for the next steps.
	depths[idx] = p_view.z;
	radii[idx] = my_radius;
    radii_xy[idx] = my_radius_x;
    radii_xy[idx + 1] = my_radius_y;
	points_xy_image[idx] = point_image;
	// Inverse 2D covariance and opacity neatly pack into one float4
//	conic_opacity[idx] = { conic.x, conic.y, conic.z, opacities[idx] };
	conic_opacity[idx] = { conic.x, conic.y, conic.z, col.w };
	tiles_touched[idx] = (rect_max.y - rect_min.y) * (rect_max.x - rect_min.x);
}

// Main rasterization method. Collaboratively works on one tile per
// block, each thread treats one pixel. Alternates between fetching 
// and rasterizing data.
template <uint32_t CHANNELS>
__global__ void __launch_bounds__(BLOCK_X * BLOCK_Y)
renderCUDA(
	const uint2* __restrict__ ranges,
	const uint32_t* __restrict__ point_list,
	int W, int H,
	const float2* __restrict__ points_xy_image,
	const float* __restrict__ features,
	const float4* __restrict__ conic_opacity,
	float* __restrict__ final_T,
	uint32_t* __restrict__ n_contrib,
	const float* __restrict__ bg_color,
	float* __restrict__ out_color)
{
	// Identify current tile and associated min/max pixel range.
	auto block = cg::this_thread_block();
	uint32_t horizontal_blocks = (W + BLOCK_X - 1) / BLOCK_X;
	uint2 pix_min = { block.group_index().x * BLOCK_X, block.group_index().y * BLOCK_Y };
	uint2 pix_max = { min(pix_min.x + BLOCK_X, W), min(pix_min.y + BLOCK_Y , H) };
	uint2 pix = { pix_min.x + block.thread_index().x, pix_min.y + block.thread_index().y };
	uint32_t pix_id = W * pix.y + pix.x;
	float2 pixf = { (float)pix.x, (float)pix.y };

	// Check if this thread is associated with a valid pixel or outside.
	bool inside = pix.x < W&& pix.y < H;
	// Done threads can help with fetching, but don't rasterize
	bool done = !inside;

	// Load start/end range of IDs to process in bit sorted list.
	uint2 range = ranges[block.group_index().y * horizontal_blocks + block.group_index().x];
	const int rounds = ((range.y - range.x + BLOCK_SIZE - 1) / BLOCK_SIZE);
	int toDo = range.y - range.x;

	// Allocate storage for batches of collectively fetched data.
	__shared__ int collected_id[BLOCK_SIZE];
	__shared__ float2 collected_xy[BLOCK_SIZE];
	__shared__ float4 collected_conic_opacity[BLOCK_SIZE];

	// Initialize helper variables
	float T = 1.0f;
	uint32_t contributor = 0;
	uint32_t last_contributor = 0;
	float C[CHANNELS] = { 0 };

	// Iterate over batches until all done or range is complete
	for (int i = 0; i < rounds; i++, toDo -= BLOCK_SIZE)
	{
		// End if entire block votes that it is done rasterizing
		int num_done = __syncthreads_count(done);
		if (num_done == BLOCK_SIZE)
			break;

		// Collectively fetch per-Gaussian data from global to shared
		int progress = i * BLOCK_SIZE + block.thread_rank();
		if (range.x + progress < range.y)
		{
			int coll_id = point_list[range.x + progress];
			collected_id[block.thread_rank()] = coll_id;
			collected_xy[block.thread_rank()] = points_xy_image[coll_id];
			collected_conic_opacity[block.thread_rank()] = conic_opacity[coll_id];
		}
		block.sync();

		// Iterate over current batch
		for (int j = 0; !done && j < min(BLOCK_SIZE, toDo); j++)
		{
			// Keep track of current position in range
			contributor++;

			// Resample using conic matrix (cf. "Surface 
			// Splatting" by Zwicker et al., 2001)
			float2 xy = collected_xy[j];
			float2 d = { xy.x - pixf.x, xy.y - pixf.y };
			float4 con_o = collected_conic_opacity[j];
			float power = -0.5f * (con_o.x * d.x * d.x + con_o.z * d.y * d.y) - con_o.y * d.x * d.y;
			if (power > 0.0f)
				continue;

			// Eq. (2) from 3D Gaussian splatting paper.
			// Obtain alpha by multiplying with Gaussian opacity
			// and its exponential falloff from mean.
			// Avoid numerical instabilities (see paper appendix).
			float alpha = min(0.99f, con_o.w * exp(power));
			if (alpha < 1.0f / 255.0f)
				continue;
			float test_T = T * (1 - alpha);
			if (test_T < 0.0001f)
			{
				done = true;
				continue;
			}

			// Eq. (3) from 3D Gaussian splatting paper.
			for (int ch = 0; ch < CHANNELS; ch++)
				C[ch] += features[collected_id[j] * CHANNELS + ch] * alpha * T;

			T = test_T;

			// Keep track of last range entry to update this
			// pixel.
			last_contributor = contributor;
		}
	}

	// All threads that treat valid pixel write out their final
	// rendering data to the frame and auxiliary buffers.
	if (inside)
	{
		final_T[pix_id] = T;
		n_contrib[pix_id] = last_contributor;
		for (int ch = 0; ch < CHANNELS; ch++) {
            out_color[ch * H * W + pix_id] = C[ch] + T * bg_color[ch];
        }
	}
}

// Main rasterization method. Collaboratively works on one tile per
// block, each thread treats one pixel. Alternates between fetching
// and rasterizing data.
// Render circles without any shading and without gaussian blur
template <uint32_t CHANNELS>
__global__ void __launch_bounds__(BLOCK_X * BLOCK_Y)
render_flatCUDA(
	const uint2* __restrict__ ranges,
	const uint32_t* __restrict__ point_list,
	int W, int H,
	const float2* __restrict__ points_xy_image,
	const float* __restrict__ features,
	const float4* __restrict__ conic_opacity,
	float* __restrict__ final_T,
	uint32_t* __restrict__ n_contrib,
	const float* __restrict__ bg_color,
    const float* viewmatrix,
	const float* projmatrix,
	const float* orig_points,
	float* __restrict__ out_color)
{
	// Identify current tile and associated min/max pixel range.
	auto block = cg::this_thread_block();
	uint32_t horizontal_blocks = (W + BLOCK_X - 1) / BLOCK_X;
	uint2 pix_min = { block.group_index().x * BLOCK_X, block.group_index().y * BLOCK_Y };
	uint2 pix_max = { min(pix_min.x + BLOCK_X, W), min(pix_min.y + BLOCK_Y , H) };
	uint2 pix = { pix_min.x + block.thread_index().x, pix_min.y + block.thread_index().y };
	uint32_t pix_id = W * pix.y + pix.x;
	float2 pixf = { (float)pix.x, (float)pix.y };

	// Check if this thread is associated with a valid pixel or outside.
	bool inside = pix.x < W&& pix.y < H;
	// Done threads can help with fetching, but don't rasterize
	bool done = !inside;

	// Load start/end range of IDs to process in bit sorted list.
	uint2 range = ranges[block.group_index().y * horizontal_blocks + block.group_index().x];
	const int rounds = ((range.y - range.x + BLOCK_SIZE - 1) / BLOCK_SIZE);
	int toDo = range.y - range.x;

	// Allocate storage for batches of collectively fetched data.
	__shared__ int collected_id[BLOCK_SIZE];
	__shared__ float2 collected_xy[BLOCK_SIZE];
	__shared__ float4 collected_conic_opacity[BLOCK_SIZE];

	// Initialize helper variables
	float T = 1.0f;
	uint32_t contributor = 0;
	uint32_t last_contributor = 0;
	float C[CHANNELS] = { 0 };

	// Iterate over batches until all done or range is complete
	for (int i = 0; i < rounds; i++, toDo -= BLOCK_SIZE)
	{
		// End if entire block votes that it is done rasterizing
		int num_done = __syncthreads_count(done);
		if (num_done == BLOCK_SIZE)
			break;

		// Collectively fetch per-Gaussian data from global to shared
		int progress = i * BLOCK_SIZE + block.thread_rank();
		if (range.x + progress < range.y)
		{
			int coll_id = point_list[range.x + progress];
			collected_id[block.thread_rank()] = coll_id;
			collected_xy[block.thread_rank()] = points_xy_image[coll_id];
			collected_conic_opacity[block.thread_rank()] = conic_opacity[coll_id];
		}
		block.sync();

		// Iterate over current batch
		for (int j = 0; !done && j < min(BLOCK_SIZE, toDo); j++)
		{
			// Keep track of current position in range
			contributor++;

			// Resample using conic matrix (cf. "Surface
			// Splatting" by Zwicker et al., 2001)
			float2 xy = collected_xy[j];
			float2 d = { xy.x - pixf.x, xy.y - pixf.y };
			float4 con_o = collected_conic_opacity[j];
			float power = -0.5f * (con_o.x * d.x * d.x + con_o.z * d.y * d.y) - con_o.y * d.x * d.y;
 			if (power > 0.0f)
 				continue;

			// Eq. (2) from 3D Gaussian splatting paper.
			// Obtain alpha by multiplying with Gaussian opacity
			// and its exponential falloff from mean.
			// Avoid numerical instabilities (see paper appendix).
            float alpha_value = min(0.99f, con_o.w * exp(power));
            float opaque_value = 1;
            float alpha = alpha_value;
            if(con_o.w > 0.5) {
                float interp_value = con_o.w * 2 - 1;
                alpha = alpha_value * (1 - interp_value) + opaque_value * interp_value;
            }

            alpha = min(0.99f, alpha);
			if (alpha < 1.0f / 255.0f)
				continue;
            if (alpha_value < 1.0f / 255.0f)
                continue;
            float test_T = T * (1 - alpha);
            if (test_T < 0.0001f)
            {
                done = true;
                continue;
            }

			float test = con_o.w * exp(power);

			// Eq. (3) from 3D Gaussian splatting paper.
			for (int ch = 0; ch < CHANNELS; ch++)
				C[ch] += features[collected_id[j] * CHANNELS + ch] * alpha * T;
//                 C[ch] = features[collected_id[j] * CHANNELS + ch] * alpha * T;
// 				C[ch] += test;



//             C[0] = 1;
//             C[1] = 0;
//             C[2] = 0;
//             C[3] = 1;

			T = test_T;
// 			T = 1.0f - test_T;

			// Keep track of last range entry to update this
			// pixel.
			last_contributor = contributor;
		}
	}

	// All threads that treat valid pixel write out their final
	// rendering data to the frame and auxiliary buffers.
	if (inside)
	{
		final_T[pix_id] = T;
		n_contrib[pix_id] = last_contributor;
		for (int ch = 0; ch < CHANNELS; ch++)
			out_color[ch * H * W + pix_id] = C[ch]; // + bg_color[ch];

// 			out_color[ch * H * W + pix_id] = T;
//             out_color[ch * H * W + pix_id] = C[ch];

	}
}

// Main rasterization method. Collaboratively works on one tile per
// block, each thread treats one pixel. Alternates between fetching
// and rasterizing data.
// Render shading
template <uint32_t CHANNELS>
__global__ void __launch_bounds__(BLOCK_X * BLOCK_Y)
render_phongShadingCUDA(
	const uint2* __restrict__ ranges,
	const uint32_t* __restrict__ point_list,
	int W, int H,
	const float2* __restrict__ points_xy_image,
	const float* __restrict__ features,
	const float4* __restrict__ conic_opacity,
	float* __restrict__ final_T,
	uint32_t* __restrict__ n_contrib,
	const float* __restrict__ bg_color,
    const float* viewmatrix,
	const float* projmatrix,
	const float* orig_points,
	const float scale_modifier,
    int* radii,
	float* __restrict__ out_color)
{
	// Identify current tile and associated min/max pixel range.
	auto block = cg::this_thread_block();
	uint32_t horizontal_blocks = (W + BLOCK_X - 1) / BLOCK_X;
	uint2 pix_min = { block.group_index().x * BLOCK_X, block.group_index().y * BLOCK_Y };
	uint2 pix_max = { min(pix_min.x + BLOCK_X, W), min(pix_min.y + BLOCK_Y , H) };
	uint2 pix = { pix_min.x + block.thread_index().x, pix_min.y + block.thread_index().y };
	uint32_t pix_id = W * pix.y + pix.x;
	float2 pixf = { (float)pix.x, (float)pix.y };

	// Check if this thread is associated with a valid pixel or outside.
	bool inside = pix.x < W&& pix.y < H;
	// Done threads can help with fetching, but don't rasterize
	bool done = !inside;

	// Load start/end range of IDs to process in bit sorted list.
	uint2 range = ranges[block.group_index().y * horizontal_blocks + block.group_index().x];
	const int rounds = ((range.y - range.x + BLOCK_SIZE - 1) / BLOCK_SIZE);
	int toDo = range.y - range.x;

	// Allocate storage for batches of collectively fetched data.
	__shared__ int collected_id[BLOCK_SIZE];
	__shared__ float2 collected_xy[BLOCK_SIZE];
	__shared__ float4 collected_conic_opacity[BLOCK_SIZE];

	// Initialize helper variables
	float T = 1.0f;
	uint32_t contributor = 0;
	uint32_t last_contributor = 0;
	float C[CHANNELS] = { 0 };

	// Iterate over batches until all done or range is complete
	for (int i = 0; i < rounds; i++, toDo -= BLOCK_SIZE)
	{
		// End if entire block votes that it is done rasterizing
		int num_done = __syncthreads_count(done);
		if (num_done == BLOCK_SIZE)
			break;

		// Collectively fetch per-Gaussian data from global to shared
		int progress = i * BLOCK_SIZE + block.thread_rank();
		if (range.x + progress < range.y)
		{
			int coll_id = point_list[range.x + progress];
			collected_id[block.thread_rank()] = coll_id;
			collected_xy[block.thread_rank()] = points_xy_image[coll_id];
			collected_conic_opacity[block.thread_rank()] = conic_opacity[coll_id];
		}
		block.sync();

		// Iterate over current batch
		for (int j = 0; !done && j < min(BLOCK_SIZE, toDo); j++)
		{
			// Keep track of current position in range
			contributor++;

			// Resample using conic matrix (cf. "Surface
			// Splatting" by Zwicker et al., 2001)
			float2 xy = collected_xy[j];
			float2 d = { xy.x - pixf.x, xy.y - pixf.y };
			float4 con_o = collected_conic_opacity[j];
			float power = -0.5f * (con_o.x * d.x * d.x + con_o.z * d.y * d.y) - con_o.y * d.x * d.y;

			// Eq. (2) from 3D Gaussian splatting paper.
			// Obtain alpha by multiplying with Gaussian opacity
			// and its exponential falloff from mean.
			// Avoid numerical instabilities (see paper appendix).
			float alpha = min(0.99f, con_o.w * exp(power));

			float test_T = T * (1 - alpha);

            glm::mat3 view_glm = glm::mat3(
                    viewmatrix[0], viewmatrix[4], viewmatrix[8],
                    viewmatrix[1], viewmatrix[5], viewmatrix[9],
                    viewmatrix[2], viewmatrix[6], viewmatrix[10]);

            glm::mat3 proj_glm = glm::mat3(
                    projmatrix[0], projmatrix[4], projmatrix[8],
                    projmatrix[1], projmatrix[5], projmatrix[9],
                    projmatrix[2], projmatrix[6], projmatrix[10]);

            glm::vec3 phong_color;
            glm::vec3 light_position_world = glm::vec3(0.0f, 0.0f, -10.0f);
            glm::vec3 light_position = proj_glm * view_glm * light_position_world;
            glm::vec3 light_color = glm::vec3(1.0f, 1.0f, 1.0f); // White light
            float ambient_intensity = 0.1f;

            glm::vec3 material_ambient = glm::vec3(0.1f, 0.1f, 0.1f);
            glm::vec3 material_diffuse = glm::vec3(0.6f, 0.6f, 0.6f);
            glm::vec3 material_specular = glm::vec3(0.8f, 0.8f, 0.8f);
            float shininess = 32.0f;

            float radius = scale_modifier;

            float r_in_pixels = float(radii[collected_id[j]]); // the size of the radius in pixels
            glm::vec2 reltc = glm::vec2(d.x, d.y) * radius;
            float dist_to_center = sqrt(reltc.x * reltc.x + reltc.y * reltc.y);
            dist_to_center = dist_to_center / r_in_pixels;

            // Calculate the surface normal
            float dx = reltc.x / r_in_pixels;  // X-distance from the pixel to the sphere center
            float dy = reltc.y / r_in_pixels; // Y-distance from the pixel to the sphere center

            if (dist_to_center <= radius) {  // Check if the pixel is inside the sphere
                float dz = sqrtf(radius * radius - dist_to_center);
//                float dz = sqrtf(radius * radius - glm::dot(reltc, reltc));
                glm::vec3 normal = normalize(glm::vec3(dx, dy, dz));  // Surface normal

                glm::vec3 view_dir = normalize(glm::vec3(viewmatrix[12], viewmatrix[13], viewmatrix[14]));
//                glm::vec3 view_dir = normalize(glm::vec3(viewmatrix[3], viewmatrix[7], viewmatrix[11]));

                // view * light_pos (-> light im view space), pixf auch in view space
                glm::vec3 frag_pos_clip = glm::vec3(pixf.x / W, pixf.y / H, dz) * 2.0f - 1.0f;
                glm::vec3 frag_pos_world = glm::inverse(view_glm) * glm::inverse(proj_glm) * frag_pos_clip;
                glm::vec3 light_dir = normalize(light_position - frag_pos_world);

                glm::vec3 reflect_dir = normalize(2.0f * glm::dot(normal, light_dir) * normal - light_dir);

                glm::vec3 ambient = ambient_intensity * material_ambient;

                glm::vec3 diffuse = material_diffuse * max(glm::dot(normal, light_dir), 0.0f);

                glm::vec3 specular = material_specular * powf(max(glm::dot(view_dir, reflect_dir), 0.0f), shininess);

                glm::vec3 object_color = glm::vec3(features[collected_id[j] * CHANNELS], features[collected_id[j] * CHANNELS + 1], features[collected_id[j] * CHANNELS + 2]);

                // Combine components
                phong_color = (ambient + diffuse + specular) * object_color;

                C[0] = phong_color.x;
                C[1] = phong_color.y;
                C[2] = phong_color.z;
                C[3] = 1.0f;

            }

			// Eq. (3) from 3D Gaussian splatting paper.
// 			for (int ch = 0; ch < CHANNELS; ch++)
// 				C[ch] = features[collected_id[j] * CHANNELS + ch];

//                 C[ch] = features[collected_id[j] * CHANNELS + ch] * alpha * T;
// 				C[ch] += test;

			T = test_T;

			// Keep track of last range entry to update this
			// pixel.
			last_contributor = contributor;
		}
	}

	// All threads that treat valid pixel write out their final
	// rendering data to the frame and auxiliary buffers.
	if (inside)
	{
		final_T[pix_id] = T;
		n_contrib[pix_id] = last_contributor;
		for (int ch = 0; ch < CHANNELS; ch++)
			out_color[ch * H * W + pix_id] = C[ch]; // + bg_color[ch];

// 			out_color[ch * H * W + pix_id] = T;
//             out_color[ch * H * W + pix_id] = C[ch];

	}
}

// Main rasterization method. Collaboratively works on one tile per
// block, each thread treats one pixel. Alternates between fetching
// and rasterizing data.
// Render shading
template <uint32_t CHANNELS>
__global__ void __launch_bounds__(BLOCK_X * BLOCK_Y)
render_gaussianBall(
	const uint2* __restrict__ ranges,
	const uint32_t* __restrict__ point_list,
	int W, int H,
	const float2* __restrict__ points_xy_image,
	const float* __restrict__ features,
	const float4* __restrict__ conic_opacity,
	float* __restrict__ final_T,
	uint32_t* __restrict__ n_contrib,
	const float* __restrict__ bg_color,
    const float* viewmatrix,
	const float* projmatrix,
	const float* orig_points,
	const float scale_modifier,
	float* __restrict__ out_color)
{
    // Identify current tile and associated min/max pixel range.
    auto block = cg::this_thread_block();
    uint32_t horizontal_blocks = (W + BLOCK_X - 1) / BLOCK_X;
    uint2 pix_min = { block.group_index().x * BLOCK_X, block.group_index().y * BLOCK_Y };
    uint2 pix_max = { min(pix_min.x + BLOCK_X, W), min(pix_min.y + BLOCK_Y , H) };
    uint2 pix = { pix_min.x + block.thread_index().x, pix_min.y + block.thread_index().y };
    uint32_t pix_id = W * pix.y + pix.x;
    float2 pixf = { (float)pix.x, (float)pix.y };

    // Check if this thread is associated with a valid pixel or outside.
    bool inside = pix.x < W&& pix.y < H;
    // Done threads can help with fetching, but don't rasterize
    bool done = !inside;

    // Load start/end range of IDs to process in bit sorted list.
    uint2 range = ranges[block.group_index().y * horizontal_blocks + block.group_index().x];
    const int rounds = ((range.y - range.x + BLOCK_SIZE - 1) / BLOCK_SIZE);
    int toDo = range.y - range.x;

    // Allocate storage for batches of collectively fetched data.
    __shared__ int collected_id[BLOCK_SIZE];
    __shared__ float2 collected_xy[BLOCK_SIZE];
    __shared__ float4 collected_conic_opacity[BLOCK_SIZE];

    // Initialize helper variables
    float T = 1.0f;
    uint32_t contributor = 0;
    uint32_t last_contributor = 0;
    float C[CHANNELS] = { 0 };

    // Iterate over batches until all done or range is complete
    for (int i = 0; i < rounds; i++, toDo -= BLOCK_SIZE)
    {
        // End if entire block votes that it is done rasterizing
        int num_done = __syncthreads_count(done);
        if (num_done == BLOCK_SIZE)
            break;

        // Collectively fetch per-Gaussian data from global to shared
        int progress = i * BLOCK_SIZE + block.thread_rank();
        if (range.x + progress < range.y)
        {
            int coll_id = point_list[range.x + progress];
            collected_id[block.thread_rank()] = coll_id;
            collected_xy[block.thread_rank()] = points_xy_image[coll_id];
            collected_conic_opacity[block.thread_rank()] = conic_opacity[coll_id];
        }
        block.sync();

        // Iterate over current batch
        for (int j = 0; !done && j < min(BLOCK_SIZE, toDo); j++)
        {
            // Keep track of current position in range
            contributor++;

            // Resample using conic matrix (cf. "Surface
            // Splatting" by Zwicker et al., 2001)
            float2 xy = collected_xy[j];
            float2 d = { xy.x - pixf.x, xy.y - pixf.y };
            float4 con_o = collected_conic_opacity[j];
            float power = -0.5f * (con_o.x * d.x * d.x + con_o.z * d.y * d.y) - con_o.y * d.x * d.y;
            if (power > 0.0f){
                continue;
            }

            // Eq. (2) from 3D Gaussian splatting paper.
            // Obtain alpha by multiplying with Gaussian opacity
            // and its exponential falloff from mean.
            // Avoid numerical instabilities (see paper appendix).
            float alpha_value = min(0.99f, con_o.w * exp(power));
            float opaque_value = 1;
            float alpha = alpha_value;
            if(con_o.w > 1.0) {
                float interp_value = con_o.w * 2 - 1;
                alpha = alpha_value * (1 - interp_value) + opaque_value * interp_value;
            }

            alpha = min(0.99f, alpha);
            if (alpha < 1.0f / 255.0f)
                continue;
            if (alpha_value < 1.0f / 255.0f)
                continue;
            float test_T = T * (1 - alpha);
            if (test_T < 0.0001f)
            {
                done = true;
                continue;
            }

            float radius = scale_modifier;

            bool inside_ellipse = exp(power) > 0.01f;
            if (inside_ellipse) {
                float dz = exp(0.35 * power);

                C[0] += features[collected_id[j] * CHANNELS] * alpha * dz * T;
                C[1] += features[collected_id[j] * CHANNELS + 1] * alpha * dz * T;
                C[2] += features[collected_id[j] * CHANNELS + 2] * alpha * dz * T;

//                C[0] = 1 - con_o.w;
//                C[1] = 0;
//                C[2] = 0;

                T = test_T;
            }

            // Keep track of last range entry to update this
            // pixel.
            last_contributor = contributor;
        }
    }

    // All threads that treat valid pixel write out their final
    // rendering data to the frame and auxiliary buffers.
    if (inside)
    {
        final_T[pix_id] = T;
        n_contrib[pix_id] = last_contributor;
        for (int ch = 0; ch < CHANNELS; ch++) {
            out_color[ch * H * W + pix_id] = C[ch] + T * bg_color[ch];
        }
    }
}

// Main rasterization method. Collaboratively works on one tile per
// block, each thread treats one pixel. Alternates between fetching
// and rasterizing data.
template <uint32_t CHANNELS>
__global__ void __launch_bounds__(BLOCK_X * BLOCK_Y)
render_gaussianBallOpt(
        const uint2* __restrict__ ranges,
        const uint32_t* __restrict__ point_list,
        int W, int H,
        const float2* __restrict__ points_xy_image,
        const float* __restrict__ features,
        const float4* __restrict__ conic_opacity,
        float* __restrict__ final_T,
        uint32_t* __restrict__ n_contrib,
        const float* __restrict__ bg_color,
        const float* viewmatrix,
        const float* projmatrix,
        const float* orig_points,
        const float scale_modifier,
        int* radii,
        int* radii_xy,
        float* __restrict__ out_color)
{
    // Identify current tile and associated min/max pixel range.
    auto block = cg::this_thread_block();
    uint32_t horizontal_blocks = (W + BLOCK_X - 1) / BLOCK_X;
    uint2 pix_min = { block.group_index().x * BLOCK_X, block.group_index().y * BLOCK_Y };
    uint2 pix_max = { min(pix_min.x + BLOCK_X, W), min(pix_min.y + BLOCK_Y , H) };
    uint2 pix = { pix_min.x + block.thread_index().x, pix_min.y + block.thread_index().y };
    uint32_t pix_id = W * pix.y + pix.x;
    float2 pixf = { (float)pix.x, (float)pix.y };

    // Check if this thread is associated with a valid pixel or outside.
    bool inside = pix.x < W&& pix.y < H;
    // Done threads can help with fetching, but don't rasterize
    bool done = !inside;

    // Load start/end range of IDs to process in bit sorted list.
    uint2 range = ranges[block.group_index().y * horizontal_blocks + block.group_index().x];
    const int rounds = ((range.y - range.x + BLOCK_SIZE - 1) / BLOCK_SIZE);
    int toDo = range.y - range.x;

    // Allocate storage for batches of collectively fetched data.
    __shared__ int collected_id[BLOCK_SIZE];
    __shared__ float2 collected_xy[BLOCK_SIZE];
    __shared__ float4 collected_conic_opacity[BLOCK_SIZE];

    // Initialize helper variables
    float T = 1.0f;
    uint32_t contributor = 0;
    uint32_t last_contributor = 0;
    float C[CHANNELS] = { 0 };

    // Iterate over batches until all done or range is complete
    for (int i = 0; i < rounds; i++, toDo -= BLOCK_SIZE)
    {
        // End if entire block votes that it is done rasterizing
        int num_done = __syncthreads_count(done);
        if (num_done == BLOCK_SIZE)
            break;

        // Collectively fetch per-Gaussian data from global to shared
        int progress = i * BLOCK_SIZE + block.thread_rank();
        if (range.x + progress < range.y)
        {
            int coll_id = point_list[range.x + progress];
            collected_id[block.thread_rank()] = coll_id;
            collected_xy[block.thread_rank()] = points_xy_image[coll_id];
            collected_conic_opacity[block.thread_rank()] = conic_opacity[coll_id];
        }
        block.sync();

        // Iterate over current batch
        for (int j = 0; !done && j < min(BLOCK_SIZE, toDo); j++)
        {
            // Keep track of current position in range
            contributor++;

            // Resample using conic matrix (cf. "Surface
            // Splatting" by Zwicker et al., 2001)
            float2 xy = collected_xy[j];
            float2 d = { xy.x - pixf.x, xy.y - pixf.y };
            float4 con_o = collected_conic_opacity[j];
            float power = -0.5f * (con_o.x * d.x * d.x + con_o.z * d.y * d.y) - con_o.y * d.x * d.y;
            if (power > 0.0f){
                C[0] = 0.0f;
                C[1] = 1.0f;
                C[2] = 0.0f;
               continue;
            }

            // Eq. (2) from 3D Gaussian splatting paper.
            // Obtain alpha by multiplying with Gaussian opacity
            // and its exponential falloff from mean.
            // Avoid numerical instabilities (see paper appendix).
            float alpha_value = min(0.99f, con_o.w * exp(power));
            float opaque_value = 1;
            float alpha = alpha_value;
            if(con_o.w > 0.5) {
                float interp_value = con_o.w * 2 - 1;
                alpha = alpha_value * (1 - interp_value) + opaque_value * interp_value;
            }

            alpha = min(0.99f, alpha);
            if (alpha < 1.0f / 255.0f)
                continue;
            if (alpha_value < 1.0f / 255.0f)
                continue;
            float test_T = T * (1 - alpha);
            if (test_T < 0.0001f)
            {
                done = true;
                continue;
            }

            float radius = scale_modifier;

            float r_in_pixels = float(radii[collected_id[j]]); // the size of the radius in pixels

            float r_in_pixels_x = float(radii_xy[collected_id[j]]);
            float r_in_pixels_y = float(radii_xy[collected_id[j] + 1]);

            if (r_in_pixels_x == 0.0f || r_in_pixels_y == 0.0f){
//                printf("CONTINUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUE");
                C[0] = 0.0f;
                C[1] = 1.0f;
                C[2] = 0.0f;
                continue;
            }

            glm::vec2 reltc = glm::vec2(d.x, d.y) * 2.0f - 1.0f;

//            printf("%f, %f d.x, d.y", d.x / r_in_pixels_x, d.y / r_in_pixels_y);
            reltc.x = reltc.x;// * r_in_pixels_x;
            reltc.y = reltc.y;// * r_in_pixels_y;
            float dist_to_center = sqrt(reltc.x * reltc.x + reltc.y * reltc.y);
            dist_to_center = dist_to_center / r_in_pixels;


            // Calculate the surface normal
//            float dx = (reltc.x / r_in_pixels_x);  // X-distance from the pixel to the sphere center
//            float dy = (reltc.y / r_in_pixels_y); // Y-distance from the pixel to the sphere center

            // Check if point is in the gaussian (ellipse)
            float normalized_x = reltc.x / r_in_pixels_x;
            float normalized_y = reltc.y / r_in_pixels_y;

            bool inside_ellipse = (normalized_x * normalized_x + normalized_y * normalized_y) <= 1.0f;

//            C[0] = con_o.x * d.x * d.x;
//            C[1] = con_o.z * d.y * d.y;
//            C[2] = 0;
//            T = test_T;


            if (inside_ellipse) {  // Check if the pixel is inside the sphere
//                float dz = sqrtf(radius - dist_to_center);
//                float dz = sqrtf(radius * radius - glm::dot(reltc, reltc));
//                float dz = sqrtf(radius * radius - (dx * dx + dy * dy));
                float dz = sqrtf(radius - dist_to_center);

                C[0] += features[collected_id[j] * CHANNELS] * alpha * dz * T;
                C[1] += features[collected_id[j] * CHANNELS + 1] * alpha * dz * T;
                C[2] += features[collected_id[j] * CHANNELS + 2] * alpha * dz * T;
//                C[3] = 1.0f;

                T = test_T;
            }
            else {
                C[0] = 1.0f;
                C[1] = 0.0f;
                C[2] = 0.0f;
                T = test_T;
            }


            // Keep track of last range entry to update this
            // pixel.
            last_contributor = contributor;
        }
    }

    // All threads that treat valid pixel write out their final
    // rendering data to the frame and auxiliary buffers.
    if (inside)
    {
        final_T[pix_id] = T;
        n_contrib[pix_id] = last_contributor;
        for (int ch = 0; ch < CHANNELS; ch++) {
            out_color[ch * H * W + pix_id] = C[ch] + T * bg_color[ch];
        }
    }
}

void FORWARD::render(int P,
	const dim3 grid, dim3 block,
	const uint2* ranges,
	const uint32_t* point_list,
	int W, int H,
	const float2* means2D,
	const float* colors,
	const float4* conic_opacity,
	float* final_T,
	uint32_t* n_contrib,
	const float* bg_color,
    const float* viewmatrix,
	const float* projmatrix,
	const float* orig_points,
	const int render_mode,
	const float scale_modifier,
    int* radii,
    int* radii_xy,
    float* out_color)
{
    if (render_mode == 0){ // phong shading
        render_phongShadingCUDA<NUM_CHANNELS> << <grid, block >> > (
            ranges,
            point_list,
            W, H,
            means2D,
            colors,
            conic_opacity,
            final_T,
            n_contrib,
            bg_color,
            viewmatrix,
            projmatrix,
            orig_points,
            scale_modifier,
            radii,
            out_color
        );
    } else if (render_mode == 1) { // flat shading
        render_flatCUDA<NUM_CHANNELS> << <grid, block >> > (
            ranges,
            point_list,
            W, H,
            means2D,
            colors,
            conic_opacity,
            final_T,
            n_contrib,
            bg_color,
            viewmatrix,
            projmatrix,
            orig_points,
            out_color
        );
    } else if (render_mode == 2) { // gaussian splatting
        renderCUDA<NUM_CHANNELS> << <grid, block >> > (
            ranges,
            point_list,
            W, H,
            means2D,
            colors,
            conic_opacity,
            final_T,
            n_contrib,
            bg_color,
            out_color);
    } else if (render_mode == 3){ // gaussian ball
        render_gaussianBall<NUM_CHANNELS> << <grid, block >> > (
            ranges,
            point_list,
            W, H,
            means2D,
            colors,
            conic_opacity,
            final_T,
            n_contrib,
            bg_color,
            viewmatrix,
            projmatrix,
            orig_points,
            scale_modifier,
            out_color
        );
    } else if (render_mode == 4) { // gaussian ball opt
        render_gaussianBallOpt<NUM_CHANNELS> << <grid, block >> > (
            ranges,
            point_list,
            W, H,
            means2D,
            colors,
            conic_opacity,
            final_T,
            n_contrib,
            bg_color,
            viewmatrix,
            projmatrix,
            orig_points,
            scale_modifier,
            radii,
            radii_xy,
            out_color
        );
    }
}

void FORWARD::preprocess(int P, int D, int M,
	const float* means3D,
	const glm::vec3* scales,
	const float scale_modifier,
	const glm::vec4* rotations,
	const float* opacities,
	bool* clamped,
	const float* cov3D_precomp,
	const float* viewmatrix,
	const float* projmatrix,
	const glm::vec3* cam_pos,
	const int W, int H,
	const float focal_x, float focal_y,
	const float tan_fovx, float tan_fovy,
	int* radii,
	int* radii_xy,
	float2* means2D,
	float* depths,
	float* cov3Ds,
	float* rgb,
	float4* conic_opacity,
	const dim3 grid,
	uint32_t* tiles_touched,
	bool prefiltered,
	const float* indices,
	const float* index_properties,
	const bool orthographic_cam,
	const float individual_opacity_factor)
{
	preprocessCUDA<NUM_CHANNELS> << <(P + 255) / 256, 256 >> > (
		P, D, M,
		means3D,
		scales,
		scale_modifier,
		rotations,
		opacities,
		clamped,
		cov3D_precomp,
		viewmatrix,
		projmatrix,
		cam_pos,
		W, H,
		tan_fovx, tan_fovy,
		focal_x, focal_y,
		radii,
		radii_xy,
		means2D,
		depths,
		cov3Ds,
		rgb,
		conic_opacity,
		grid,
		tiles_touched,
		prefiltered,
		indices,
		index_properties,
		orthographic_cam,
		individual_opacity_factor
		);
}